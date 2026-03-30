import contextlib
from functools import partial
import pathlib
import shutil
import traceback
import asyncio
import datetime
import logging
import os
import os.path
import sys
from pathlib import Path
import multiprocessing
import time

import xconf
from starlette.endpoints import WebSocketEndpoint
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import orjson
import toml
import uvicorn
from astroplan import FixedTarget, Observer
from astropy.coordinates import EarthLocation
from astropy.time import Time
from purepyindi2 import messages, constants
import purepyindi2
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles

from watchdog import observers
from watchdog.events import FileSystemEventHandler

from .constants import (
    INSTRUMENT_CONFIG_ROOT, InstrumentLayouts, SITE_LOCATION,
    CONFIG_FILENAME, INSTGRAPH_FILE_PATH, OBS_ROOT
)
from .utils import OrjsonResponse

log = logging.getLogger(__name__)

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
    __version__ = f.read().strip()

LCO_SITE = Observer.at_site('Las Campanas Observatory')
LCO_COORDINATES = EarthLocation.of_site(SITE_LOCATION)

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

static_folder_name = "static"
static_path = (Path(__file__).parent / static_folder_name).resolve()

class NotFound(HTTPException):
    def __init__(self, *args, **kwargs):
        super().__init__(404, *args, **kwargs)

class SupViews:
    def __init__(self, app):
        self.app : 'WebInterface' = app

    async def light_path(self, request):
        light_path_config = INSTRUMENT_CONFIG_ROOT / 'light_path.toml'
        if not light_path_config.exists():
            light_path_config = Path(__file__).parent / 'light_path_ex.toml'

        with open(light_path_config) as fh:
            light_path_dict = toml.loads(fh.read())
        return OrjsonResponse(light_path_dict)

    async def indi(self, request):
        return OrjsonResponse(self.app.indi_client.to_serializable()['devices'])

    async def catch_all(self, request):
        path = request.path_params['path']
        real_path = (static_path / path).resolve()

        if static_path in real_path.parents:  # prevent traversal vulnerability
            if real_path.exists():
                return FileResponse(real_path.as_posix())
        else:
            log.warning(f'Attempted directory traversal with path {path}')
        raise NotFound("No route or file at this URL")

    async def index(self, request):
        return FileResponse((static_path / 'index.html').as_posix())

    async def instgraph(self, request):
        return FileResponse(self.app.instgraph_file_path)

    async def config(self, request):
        config = xconf.config_to_dict(self.app)
        return OrjsonResponse(config)

    async def obs_list(self, request):
        """Paginated directory listing under the obs root.

        Query params:
            path  - relative path within obs root (default: '')
            offset - pagination offset (default: 0)
            limit  - max entries to return (default: 200)
        """
        import stat as stat_mod
        rel = request.query_params.get('path', '')
        offset = int(request.query_params.get('offset', '0'))
        limit = min(int(request.query_params.get('limit', '200')), 1000)

        obs_root = Path(self.app.obs_root).resolve()
        target = (obs_root / rel).resolve()

        # prevent traversal outside obs_root
        if obs_root not in target.parents and target != obs_root:
            raise NotFound('Invalid path')
        if not target.is_dir():
            raise NotFound('Not a directory')

        entries = []
        total = 0
        try:
            with os.scandir(target) as scanner:
                # Collect lightweight tuples: (is_dir, name_lower, name, full_path)
                # DirEntry.is_dir() is cached from scandir, no extra syscall
                all_entries = [(not e.is_dir(), e.name.lower(), e.name, e.path, e.is_dir()) for e in scanner]
            all_entries.sort()
            total = len(all_entries)
            for _, _, name, full_path, is_dir in all_entries[offset:offset + limit]:
                try:
                    st = os.stat(full_path)
                    entries.append({
                        'name': name,
                        'is_dir': is_dir,
                        'size': st.st_size if not is_dir else None,
                        'mtime': st.st_mtime,
                    })
                except OSError:
                    continue
        except PermissionError:
            raise HTTPException(403, detail='Permission denied')

        return OrjsonResponse({
            'path': rel,
            'entries': entries,
            'total': total,
            'offset': offset,
            'limit': limit,
        })

    async def obs_file(self, request):
        """Serve raw FITS image data as binary (float32 buffer + dimensions)."""
        from astropy.io import fits as astropy_fits
        rel = request.query_params.get('path', '')
        obs_root = Path(self.app.obs_root).resolve()
        target = (obs_root / rel).resolve()

        if obs_root not in target.parents and target != obs_root:
            raise NotFound('Invalid path')
        if not target.is_file():
            raise NotFound('Not a file')

        try:
            with astropy_fits.open(str(target)) as hdul:
                # find the first ImageHDU with data
                data = None
                for hdu in hdul:
                    if hdu.data is not None and hdu.data.ndim >= 2:
                        data = hdu.data
                        break
                if data is None:
                    raise HTTPException(400, detail='No image data found in FITS file')

                # flatten to 2D if needed (take first 2D slice)
                while data.ndim > 2:
                    data = data[0]

                height, width = data.shape
                arr = np.ascontiguousarray(data, dtype=np.float32)
                buf = arr.tobytes()
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            log.error(f'Error reading FITS file {target}: {e}')
            raise HTTPException(500, detail='Error reading FITS file')

        from starlette.responses import Response
        import struct
        # header: width (u32) + height (u32) then float32 pixels
        header = struct.pack('<II', width, height)
        return Response(
            content=header + buf,
            media_type='application/octet-stream',
            headers={'X-Image-Width': str(width), 'X-Image-Height': str(height)},
        )

    async def obs_header(self, request):
        """Return the FITS header as JSON key-value pairs."""
        from astropy.io import fits as astropy_fits
        rel = request.query_params.get('path', '')
        obs_root = Path(self.app.obs_root).resolve()
        target = (obs_root / rel).resolve()

        if obs_root not in target.parents and target != obs_root:
            raise NotFound('Invalid path')
        if not target.is_file():
            raise NotFound('Not a file')

        try:
            with astropy_fits.open(str(target)) as hdul:
                cards = []
                for hdu_idx, hdu in enumerate(hdul):
                    hdu_cards = []
                    for card in hdu.header.cards:
                        keyword = card.keyword
                        value = card.value
                        comment = card.comment
                        # convert non-serializable values to strings
                        if not isinstance(value, (str, int, float, bool, type(None))):
                            value = str(value)
                        hdu_cards.append({
                            'keyword': keyword,
                            'value': value,
                            'comment': comment,
                        })
                    cards.append({'hdu': hdu_idx, 'name': hdu.name, 'cards': hdu_cards})
        except Exception as e:
            log.error(f'Error reading FITS header {target}: {e}')
            raise HTTPException(500, detail='Error reading FITS file')

        return OrjsonResponse(cards)

    async def obs_download(self, request):
        """Serve the raw FITS file for download."""
        rel = request.query_params.get('path', '')
        obs_root = Path(self.app.obs_root).resolve()
        target = (obs_root / rel).resolve()

        if obs_root not in target.parents and target != obs_root:
            raise NotFound('Invalid path')
        if not target.is_file():
            raise NotFound('Not a file')

        return FileResponse(
            str(target),
            filename=target.name,
            media_type='application/octet-stream',
        )

    async def sun_and_moon(self, request):
        current_time = Time(utc_now())
        payload = {
            'solar_system': {
                'moon': {
                    'rise': LCO_SITE.moon_rise_time(current_time).to_value('iso'),
                    'set': LCO_SITE.moon_set_time(current_time).to_value('iso'),
                },
                'sun': {
                    'rise': LCO_SITE.sun_rise_time(current_time).to_value('iso'),
                    'set': LCO_SITE.sun_set_time(current_time).to_value('iso'),
                },
            }}
        return OrjsonResponse(payload)

    async def observability_curves(self, request):
        ra_str, dec_str = request.query_params.get('ra', None), request.query_params.get('dec', None)
        target_name = request.query_params.get('target_name', None)

        if (ra_str is None or dec_str is None) and (target_name is None):
            raise HTTPException(400)
        if ra_str is None and dec_str is None:
            target = FixedTarget.from_name(target_name)
        else:
            coord = SkyCoord(ra=float(ra_str)*u.deg, dec=float(dec_str)*u.deg)
            target = FixedTarget(coord, label=f"RA: {ra_str}, Dec: {dec_str}")
        current_time = Time(utc_now())
        sample_times = current_time + np.linspace(-12, 12, 100)*u.hour
        altitude = LCO_SITE.altaz(sample_times, target).alt
        p_angle = LCO_SITE.parallactic_angle(sample_times, target)
        payload = {
            'parallactic_angles': [
                {'x': ts.to_value('iso'), 'y': angle}
                for (ts, angle) in zip(sample_times, p_angle.to(u.degree).value)
            ],
            'altitudes': [
                {'x': ts.to_value('iso'), 'y': angle}
                for (ts, angle) in zip(sample_times, altitude.to(u.degree).value)
            ],
        }

        try:
            serialized = OrjsonResponse(payload)
        except TypeError as e:
            raise Exception(f"Couldn't serialize {payload=} because {e}")
        return serialized


class INDIUpdateBatcher:
    def __init__(self, client_instance):
        self.client_instance = client_instance
        self.properties_to_update = set()
        self.properties_to_delete = set()
        self.logs = []
    async def process_update(self, message : messages.IndiMessage):
        if isinstance(message, messages.DelProperty):
            prop_to_del = (message.device, message.name if message.name is not None else "*")
            self.properties_to_delete.add(prop_to_del)
        elif isinstance(message, messages.IndiDefMessage):
            key = (message.device, message.name)
            if key in self.properties_to_delete:
                self.properties_to_delete.remove(key)
            key = (message.device, "*")
            if key in self.properties_to_delete:
                self.properties_to_delete.remove(key)
            self.properties_to_update.add((message.device, message.name))
        elif isinstance(message, messages.IndiSetMessage):
            self.properties_to_update.add((message.device, message.name))
        elif isinstance(message, messages.Message):
            self.logs.append(message)
    def _get_serializable(self, device_name, property_name):
        return self.client_instance.devices[device_name].properties[property_name].to_serializable()
    async def generate_batch(self):
        updates = {}
        deletions = []

        updated_not_deleted = self.properties_to_update - self.properties_to_delete
        for device_name, property_name in updated_not_deleted:
            if (
                (device_name, property_name) in self.properties_to_delete or
                (device_name, "*") in self.properties_to_delete
            ):
                continue
            try:
                updates[f'{device_name}.{property_name}'] = self.client_instance[f'{device_name}.{property_name}'].to_serializable()
            except KeyError:
                # race condition where device or property can be deleted
                # before the batch gets sent
                continue
        for device_name, property_name in self.properties_to_delete:
            deletions.append(f'{device_name}.{property_name}')

        batch = {
            'updates': updates,
            'deletions': deletions,
            'connected': self.client_instance.status == constants.ConnectionStatus.CONNECTED,
            'logs': self.logs,
        }
        self.properties_to_delete = set()
        self.properties_to_update = set()
        self.logs = []
        return batch

class AppWebSocketEndpoint(WebSocketEndpoint):
    """Add a leading 'app' argument to let methods reference a containing app
    """
    def __init__(self, cli : 'WebInterface', *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cli = cli

class SupWebSocket(AppWebSocketEndpoint):
    encoding = "bytes"
    async def on_connect(self, websocket):
        self.cli._connected_clients.append(websocket)
        await websocket.accept()
        log.debug("Sending indi init payload")
        await websocket.send_bytes(orjson.dumps({
            'action': 'indi_init',
            'payload': self.cli.indi_client.to_serializable()['devices'],
        }))
        log.debug("Sending instgraph init payload")
        # await websocket.send_bytes(orjson.dumps({
        #     'action': 'instgraph_updated',
        #     'payload': {'file': INSTGRAPH_FILE_PATH.name},
        # }))

    async def on_indi_new(self, websocket, payload):
        if not (
            'device' in payload and
            'property' in payload and
            'element' in payload and
            'value' in payload
        ):
            log.error("Received invalid message: {data_obj}")
            return
        try:
            value = constants.parse_string_into_any_indi_value(payload['value'])
            self.cli.indi_client[f"{payload['device']}.{payload['property']}.{payload['element']}"] = value
        except Exception as e:
            log.exception(f"Swallowed exception: Couldn't set INDI value from {payload}")


    async def on_receive(self, websocket, data):
        data_obj = orjson.loads(data)
        log.debug(f"Recv from {websocket.client.host}: {data_obj}")
        payload = data_obj.get('payload')
        action = data_obj.get('action')
        if action == 'indi_new':
            await self.on_indi_new(websocket, payload)

    async def on_disconnect(self, websocket, close_code):
        try:
            idx = self.cli._connected_clients.index(websocket)
            self.cli._connected_clients.pop(idx)
        except ValueError:
            pass

class LogStreamWebSocket(AppWebSocketEndpoint):
    encoding = "bytes"

    async def on_connect(self, websocket):
        await websocket.accept()
        unit = self.cli.log_unit
        use_journalctl = unit and shutil.which("journalctl") is not None
        if use_journalctl:
            self._proc = await asyncio.create_subprocess_exec(
                "journalctl", "-f", "-u", unit, "--no-pager", "-o", "short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            self._task = asyncio.create_task(self._stream_lines(websocket, self._proc.stdout))
        else:
            self._proc = None
            self._task = asyncio.create_task(self._stream_demo(websocket))

    async def _stream_lines(self, websocket, stream):
        try:
            async for line in stream:
                await websocket.send_bytes(line.rstrip(b"\n"))
        except Exception:
            pass

    async def _stream_demo(self, websocket):
        import random
        demo_messages = [
            "lookyloo[1234]: Processing target HD 12345",
            "lookyloo[1234]: Exposure 30.0s band=z",
            "lookyloo[1234]: Writing /home/guestobs/obs/2025-01-15/hd12345_z_0001.fits",
            "lookyloo[1234]: Slewing to RA=12:34:56 DEC=+12:34:56",
            "lookyloo[1234]: AO loop closed, Strehl=0.42",
            "lookyloo[1234]: Pipeline quicklook ready",
            "lookyloo[1234]: ADC correction applied: PA=127.3",
            "lookyloo[1234]: Coronagraph insert: lyot_05",
            "lookyloo[1234]: DM flat set: dmflat_20250115",
            "lookyloo[1234]: Sky subtraction complete",
        ]
        try:
            while True:
                ts = datetime.datetime.now().strftime("%b %d %H:%M:%S")
                msg = random.choice(demo_messages)
                await websocket.send_bytes(f"{ts} exao2 {msg}".encode())
                await asyncio.sleep(random.uniform(0.5, 3.0))
        except Exception:
            pass

    async def on_receive(self, websocket, data):
        pass

    async def on_disconnect(self, websocket, close_code):
        if hasattr(self, "_task"):
            self._task.cancel()
        if hasattr(self, "_proc") and self._proc is not None:
            try:
                self._proc.terminate()
            except ProcessLookupError:
                pass

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, web_interface, file_path_to_watch, debouncing_interval_sec, loop):
        self.web_interface = web_interface
        self.file_path_to_watch = file_path_to_watch
        self.debouncing_interval_sec = debouncing_interval_sec
        self.loop = loop
        self._last_modified_time = 0

    def on_modified(self, event):
        """Trigger only if the specific file is modified."""
        if event.is_directory:
            return

        current_time = time.time()

        # Check if enough time has passed since the last update
        if current_time - self._last_modified_time < self.debouncing_interval_sec:
            return

        self._last_modified_time = current_time

        log.debug(f"Update noticed on file {event.src_path}")
        if os.path.realpath(event.src_path) == os.path.realpath(self.file_path_to_watch):
            log.debug(f"Update noticed on target file {event.src_path}")
            asyncio.run_coroutine_threadsafe(
                self.web_interface.emit_instgraph_update(),
                self.loop
            )

@xconf.config
class IndiConfig:
    hostname : str = xconf.field(default="localhost", help="Hostname of INDI server")
    port : int = xconf.field(default=7624, help="Port number of INDI server")

@xconf.config
class WebInterface(xconf.Command):
    @classmethod
    def get_default_config_path(cls) -> pathlib.Path:
        return INSTRUMENT_CONFIG_ROOT / CONFIG_FILENAME

    """Instrument web interface"""
    layout : InstrumentLayouts = xconf.field(default=InstrumentLayouts.MAGAOX)
    bind_host : str = xconf.field(default="127.0.0.1", help="Listening address (0.0.0.0 for all)")
    bind_port : int = xconf.field(default=9191, help="Listening TCP port")
    indi : IndiConfig = xconf.field(default_factory=IndiConfig)
    potemkin : bool = xconf.field(
        default=False,
        help="Whether to load a system snapshot for testing (disables connection to INDI server)"
    )
    debug_mode : bool = xconf.field(default=True, help="Initialize Starlette framework in debug mode")
    batch_update_interval_sec : float = xconf.field(
        default=0.2,
        help="How often to emit a batch of updates over the websocket to connected clients"
    )
    debouncing_interval_sec : float = xconf.field(
        default=0.2,
        help="How long to wait before sending a message over the websocket that the instGraph file has updated"
    )
    instgraph_file_path : str = xconf.field(default=INSTGRAPH_FILE_PATH, help="Absolute path of .drawio file that instGraph updates")
    obs_root : str = xconf.field(default=OBS_ROOT, help="Root directory for observation file browsing")
    log_unit : str = xconf.field(default="lookyloo", help="systemd unit name whose journal to stream (empty to disable)")

    def __post_init__(self):
        self._running_tasks = set()
        self._connected_clients = []
        self._last_instgraph_update = 0
        self._posix_instgraph_file_path = pathlib.Path(self.instgraph_file_path)

    async def emit_indi_updates(self):
        while True:
            try:
                batch = await self.indi_batcher.generate_batch()
                for websocket in self._connected_clients:
                    try:
                        await websocket.send_bytes(orjson.dumps({'action': 'indi_batch_update', 'payload': batch}))
                    except Exception as e:
                        log.debug(f"Swallowed exception in websocket.send_bytes: {type(e)} {e}")
            except Exception as e:
                log.warning(f"Exception in emit_indi_updates(): {type(e)=} {e}")
                traceback.print_exc(file=sys.stdout)
            await asyncio.sleep(self.batch_update_interval_sec)

    async def emit_instgraph_update(self):
        """Send file update notification via WebSocket."""
        try:
            for websocket in self._connected_clients:
                try:
                    log.debug(f"Sending instgraph udpate trigger for file {self._posix_instgraph_file_path.name}")
                    await websocket.send_bytes(orjson.dumps({'action': 'instgraph_updated', 'payload': {'file': self._posix_instgraph_file_path.name}}))
                except Exception as e:
                    log.debug(f"Swallowed exception in websocket.send_bytes: {type(e)} {e}")
        except Exception as e:
            log.warning(f"Exception in emit_instgraph_updated(): {type(e)=} {e}")
            traceback.print_exc(file=sys.stdout)
        await asyncio.sleep(self.batch_update_interval_sec)

    async def start_file_watcher(self, file_path_to_watch=None):
        """Run the watchdog observer as an async background task."""
        loop = asyncio.get_event_loop()

        file_path_to_watch = file_path_to_watch or self._posix_instgraph_file_path
        event_handler = FileChangeHandler(self, file_path_to_watch, self.debouncing_interval_sec, loop)
        observer = observers.Observer()
        observer.schedule(event_handler, file_path_to_watch.parent, recursive=False)
        observer.start()

        try:
            await asyncio.to_thread(observer.join)  # Run observer in a separate thread
        finally:
            observer.stop()
            observer.join()

    async def trigger_get_properties(self, message):
        if message is constants.ConnectionStatus.CONNECTED:
            log.debug(f"Trigger get properties: {message}")
            self.indi_client.get_properties()

    async def spawn_tasks(self, app: Starlette, task_group: asyncio.TaskGroup):
        conn = purepyindi2.AsyncIndiTcpConnection(host=self.indi.hostname, port=self.indi.port)
        self.indi_client = purepyindi2.IndiClient(conn)
        self._running_tasks.add(task_group.create_task(self.indi_client.connection.add_async_callback(constants.TransportEvent.connection, self.trigger_get_properties)))

        self.indi_batcher = INDIUpdateBatcher(self.indi_client)
        self._running_tasks.add(task_group.create_task(self.indi_client.connection.add_async_callback(constants.TransportEvent.inbound, self.indi_batcher.process_update)))

        self._running_tasks.add(task_group.create_task(self.start_file_watcher()))

        indi_coro = self.indi_client.connection.run(reconnect_automatically=True)
        self._running_tasks.add(task_group.create_task(indi_coro))

        emit_indi_updates_coro = self.emit_indi_updates()
        self._running_tasks.add(task_group.create_task(emit_indi_updates_coro))

    async def cancel_tasks(self):
        await self.indi_client.connection.stop()
        for task in self._running_tasks:
            log.info(f"Cancelling task: {task}")
            task.cancel()

    def main(self):
        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette):
            async with asyncio.TaskGroup() as tg:
                await self.spawn_tasks(app, tg)
                log.info("Started background tasks")
                yield
                log.info("Stopping background tasks...")
                await self.cancel_tasks()
        self.views = SupViews(self)
        self.app = Starlette(
            debug=self.debug_mode,
            routes=[
                Route('/', endpoint=self.views.index),
                Route('/indi', endpoint=self.views.indi),
                Route('/light-path', endpoint=self.views.light_path),
                Route('/sun-moon', endpoint=self.views.sun_and_moon),
                Route('/observability-curves', endpoint=self.views.observability_curves),
                Route('/config', endpoint=self.views.config),
                Route('/obs/list', endpoint=self.views.obs_list),
                Route('/obs/file', endpoint=self.views.obs_file),
                Route('/obs/header', endpoint=self.views.obs_header),
                Route('/obs/download', endpoint=self.views.obs_download),
                WebSocketRoute('/websocket', endpoint=partial(SupWebSocket, self)),
                WebSocketRoute('/ws/logs', endpoint=partial(LogStreamWebSocket, self)),
                Route("/instgraph", endpoint=self.views.instgraph),
                Route('/{path:path}', endpoint=self.views.catch_all),
            ],
            lifespan=lifespan,
            middleware=[
                Middleware(GZipMiddleware),
                Middleware(CORSMiddleware, allow_origins=['*'])
            ]
        )
        uvicorn.run(self.app, host=self.bind_host, port=self.bind_port)
