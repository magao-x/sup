import contextlib
from functools import lru_cache, partial
import pathlib
import shutil
import traceback
import asyncio
import datetime
import logging
import os
import os.path
import sys
import time
from pathlib import Path
import multiprocessing

import xconf
from starlette.endpoints import WebSocketEndpoint
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
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
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles

from watchdog import observers
from watchdog.events import FileSystemEventHandler

from .constants import (
    INSTRUMENT_CONFIG_ROOT, InstrumentLayouts, SITE_LOCATION,
    CONFIG_FILENAME, INSTGRAPH_FILE_PATH, OBS_ROOT,
    AUDIBLE_ALERTS_DEVICE, AUDIBLE_ALERTS_CACHE_ROOT,
    AUDIBLE_ALERTS_TEMP_SUBDIR, AUDIBLE_ALERTS_CLIP_MAX_AGE_SEC,
)
from .utils import OrjsonResponse

log = logging.getLogger(__name__)

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
    __version__ = f.read().strip()

LCO_SITE = Observer.at_site('Las Campanas Observatory')
LCO_COORDINATES = EarthLocation.of_site(SITE_LOCATION)
# Hours by which local solar time leads UTC at the site (negative, west of
# Greenwich). Used to bucket moments into observing nights.
SITE_SOLAR_OFFSET_HOURS = LCO_COORDINATES.lon.to_value(u.hourangle)

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

def observing_night(when):
    """Identify which night of observing a moment belongs to.

    Bucketed at local solar noon rather than at UTC midnight, which falls in
    the middle of the night here and would split one night's observing across
    two keys.
    """
    local_solar = when + datetime.timedelta(hours=SITE_SOLAR_OFFSET_HOURS)
    return (local_solar - datetime.timedelta(hours=12)).date()

# How many target names to remember. Far more than a night's observing list,
# so in practice it bounds memory rather than evicting anything that matters.
TARGET_NAME_CACHE_SIZE = 256

@lru_cache(maxsize=TARGET_NAME_CACHE_SIZE)
def resolve_target_name(name):
    """Look up a target's coordinates by name, or None if there is no such target.

    The lookup goes out to Sesame over the network, and catalog positions
    don't change between requests, so answers are remembered: both a position
    and the news that the name doesn't exist. Failures to get an answer at all
    --- timeouts, an unreachable service --- propagate as exceptions, which
    lru_cache does not remember, so the next request tries again.
    """
    try:
        return SkyCoord.from_name(name)
    except NameResolveError as e:
        # astropy raises the same exception whether Sesame answered "no such
        # object" or could not be reached; only the message tells them apart.
        # tests/test_target_name_cache.py pins this against the installed
        # astropy, so a change in wording fails a test rather than turning
        # outages into cached non-existence.
        if str(e).startswith("Unable to find coordinates"):
            return None
        raise

# Both the URL the graph is served at and the name a browser saves it under.
INSTGRAPH_DOWNLOAD_NAME = "instgraph.drawio"

static_folder_name = "static"
static_path = (Path(__file__).parent / static_folder_name).resolve()

class NotFound(HTTPException):
    def __init__(self, *args, **kwargs):
        super().__init__(404, *args, **kwargs)

class SupViews:
    def __init__(self, app):
        self.app : 'WebInterface' = app
        self._sun_and_moon_for_night = None
        # Held so that a burst of requests at the start of a night produces one
        # computation rather than one per request.
        self._sun_and_moon_lock = asyncio.Lock()

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
            if real_path.is_file():
                return FileResponse(real_path.as_posix())
            # Nothing on disk, so this is either a client-side route or a
            # genuinely missing asset. The router uses history mode, meaning
            # a reload or a bookmark of e.g. /instgraph arrives here as a
            # real request; hand back the app and let the router resolve the
            # path. A request carrying a file extension is an asset request,
            # though, and answering those with HTML would turn a missing
            # script into a baffling MIME type error instead of a 404.
            if not real_path.suffix:
                return await self.index(request)
        else:
            log.warning(f'Attempted directory traversal with path {path}')
        raise NotFound("No route or file at this URL")

    async def index(self, request):
        return FileResponse((static_path / 'index.html').as_posix())

    async def instgraph(self, request):
        """Serve the instrument state graph.

        Named for the file it returns rather than for the tab that shows it,
        so it doesn't collide with the client-side /instgraph route and so a
        browser pointed straight at it saves something sensibly named.
        """
        graph_path = Path(self.app.instgraph_file_path)
        if not graph_path.is_file():
            raise NotFound(f"No instrument state graph at {graph_path}")
        # The file is replaced in-place by the writer, so a cached copy is
        # always a stale copy. Clients also cache-bust with ?rev=, but belt
        # and braces: intermediate proxies don't see the query string as
        # meaningful unless we say so.
        return FileResponse(graph_path.as_posix(), filename=INSTGRAPH_DOWNLOAD_NAME, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        })

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

        # Off the event loop: a night's worth of exposures is thousands of
        # entries and a stat() apiece, and every millisecond spent here is a
        # millisecond in which no websocket update reaches anyone.
        def read_directory():
            entries = []
            with os.scandir(target) as scanner:
                # Collect lightweight tuples: (is_dir, name_lower, name, full_path)
                # DirEntry.is_dir() is cached from scandir, no extra syscall
                all_entries = [(not e.is_dir(), e.name.lower(), e.name, e.path, e.is_dir()) for e in scanner]
            all_entries.sort()
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
            return entries, len(all_entries)

        try:
            entries, total = await asyncio.to_thread(read_directory)
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

        # Reading and converting a detector frame is slow enough to be felt by
        # every other connected client if it happens on the event loop.
        def read_image():
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
                return width, height, arr.tobytes()

        try:
            width, height, buf = await asyncio.to_thread(read_image)
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

        def read_header():
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
                return cards

        try:
            cards = await asyncio.to_thread(read_header)
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

    async def audible_alerts_clip(self, request):
        """Serve one audio clip for the browser-side audible alerts player.

        The audibleAlerts device names clips by content: synthesized speech is
        named for a hash of its text and voice, and recordings are copied into
        the cache under their own names. A given URL therefore always means the
        same audio, so browsers can keep clips indefinitely --- which is most of
        the point, since random utterances, soundboard buttons, and walkups
        repeat constantly, and a cached clip plays with no fetch latency.

        The exception is the temp/ subdirectory, which holds speech whose text
        was substituted at playback time. Those are one-offs, and the device
        empties the directory when it restarts, so they get a short lifetime
        instead of an immutable one.
        """
        rel = request.path_params['path']
        cache_root = Path(self.app.audible_alerts_cache_root).resolve()
        target = (cache_root / rel).resolve()

        if cache_root not in target.parents:  # prevent traversal vulnerability
            log.warning(f'Attempted directory traversal with path {rel}')
            raise NotFound('No audio clip at this URL')
        if not target.is_file():
            raise NotFound('No audio clip at this URL')

        if (cache_root / AUDIBLE_ALERTS_TEMP_SUBDIR) in target.parents:
            cache_control = 'public, max-age=300'
        else:
            cache_control = f'public, max-age={AUDIBLE_ALERTS_CLIP_MAX_AGE_SEC}, immutable'

        # Passing stat_result gets the ETag onto the response at construction
        # time, where we can compare it. Starlette computes one but leaves
        # conditional requests to StaticFiles, and 'immutable' means this
        # rarely fires --- but a browser that evicted the body while keeping
        # the validator shouldn't have to re-download the audio.
        stat_result = target.stat()
        # Named explicitly rather than guessed: the platform mimetypes table
        # calls .wav audio/x-wav, which Safari is fussier about than audio/wav.
        media_type = 'audio/wav' if target.suffix.lower() == '.wav' else None
        response = FileResponse(
            target.as_posix(),
            stat_result=stat_result,
            media_type=media_type,
            headers={'Cache-Control': cache_control},
        )
        etag = response.headers.get('etag')
        if etag is not None and request.headers.get('if-none-match') == etag:
            return Response(status_code=304, headers={
                'Cache-Control': cache_control,
                'ETag': etag,
            })
        return response

    async def sun_and_moon(self, request):
        """Rise and set times for the sun and moon, once per observing night.

        These move by minutes a day and are solved iteratively, so computing
        them per request is both slow and pointless. One answer per night is
        the granularity the page is actually about, and it has the side
        benefit that the displayed times stop drifting between requests.

        The one computation per night still happens on a worker thread: it
        takes long enough that doing it on the event loop would stall every
        websocket on the server, which is precisely what a new night's first
        request would otherwise do.
        """
        tonight = observing_night(utc_now())
        async with self._sun_and_moon_lock:
            if self._sun_and_moon_for_night is None or self._sun_and_moon_for_night[0] != tonight:
                def compute():
                    current_time = Time(utc_now())
                    return {
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
                log.debug(f"Computing sun and moon times for the night of {tonight}")
                self._sun_and_moon_for_night = (tonight, await asyncio.to_thread(compute))
        return OrjsonResponse(self._sun_and_moon_for_night[1])

    async def observability_curves(self, request):
        ra_str, dec_str = request.query_params.get('ra', None), request.query_params.get('dec', None)
        target_name = request.query_params.get('target_name', None)

        if (ra_str is None or dec_str is None) and (target_name is None):
            raise HTTPException(400)

        # Resolving a name goes over the network (when not cached), and the
        # altaz sampling that follows is not cheap either. Either one on the
        # event loop stalls every websocket on the server for its duration ---
        # a name lookup against an unreachable service for as long as it takes
        # to time out.
        def resolve_and_sample():
            if ra_str is None and dec_str is None:
                coord = resolve_target_name(target_name.strip())
                if coord is None:
                    raise NotFound(detail=f"No target named {target_name!r}")
                target = FixedTarget(coord, name=target_name)
            else:
                coord = SkyCoord(ra=float(ra_str)*u.deg, dec=float(dec_str)*u.deg)
                target = FixedTarget(coord, label=f"RA: {ra_str}, Dec: {dec_str}")
            current_time = Time(utc_now())
            sample_times = current_time + np.linspace(-12, 12, 100)*u.hour
            return (
                sample_times,
                LCO_SITE.altaz(sample_times, target).alt,
                LCO_SITE.parallactic_angle(sample_times, target),
            )

        sample_times, altitude, p_angle = await asyncio.to_thread(resolve_and_sample)
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
            # Stamped so a client can separate how long a batch took to arrive
            # from how far apart the two clocks are: the offset itself is
            # unknowable, but its *variation* is exactly the delivery delay.
            'sent_at': utc_now(),
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

class WebSocketClient:
    """One connected browser, and the updates still waiting to reach it.

    Each client drains a queue of its own, so broadcasting is a non-blocking
    enqueue and a browser that has stopped draining --- a laptop on bad wifi, a
    tab on the far side of an ocean --- costs only itself. Waiting on one
    client would cost everybody twice over: the other clients wait their turn
    behind it, and the batcher keeps accumulating meanwhile, so the batch that
    eventually goes out is larger and slower to send than it would have been.

    A client that falls far enough behind is disconnected rather than allowed
    to queue forever. The frontend reconnects on its own and is sent a full
    snapshot, which is the same state it would have rebuilt from the backlog.
    """
    def __init__(self, websocket, max_pending, slow_send_warning_sec):
        self.websocket = websocket
        self.outbound = asyncio.Queue(maxsize=max_pending)
        self.slow_send_warning_sec = slow_send_warning_sec
        self.sender = None
        self.overflowed = False
        self._disconnecting = None

    @property
    def where(self):
        peer = getattr(self.websocket, 'client', None)
        return f"{peer.host}:{peer.port}" if peer is not None else "unknown client"

    def start(self):
        self.sender = asyncio.create_task(self._send_pending())

    def send(self, payload: bytes):
        """Hand this client a payload without waiting for it to be written."""
        if self.overflowed:
            return
        try:
            self.outbound.put_nowait(payload)
        except asyncio.QueueFull:
            self.overflowed = True
            log.warning(
                f"Disconnecting {self.where}: {self.outbound.maxsize} updates queued "
                f"without draining. It will reconnect and resync, rather than keep a "
                f"backlog that can only grow."
            )
            self._disconnecting = asyncio.create_task(self._close_websocket())

    async def _send_pending(self):
        while True:
            payload = await self.outbound.get()
            started_at = time.monotonic()
            try:
                await self.websocket.send_bytes(payload)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.debug(f"Swallowed exception sending to {self.where}: {type(e)} {e}")
                return
            elapsed = time.monotonic() - started_at
            if elapsed > self.slow_send_warning_sec:
                # Costs only this client, but it is still the thing to look
                # for when someone reports the web UI lagging for them.
                log.warning(
                    f"Slow websocket send: {elapsed:.2f}s to {self.where} for "
                    f"{len(payload)} bytes, {self.outbound.qsize()} updates queued behind it."
                )

    async def _close_websocket(self):
        try:
            await self.websocket.close()
        except Exception as e:
            log.debug(f"Swallowed exception closing {self.where}: {type(e)} {e}")

    def stop(self):
        if self.sender is not None:
            self.sender.cancel()
            self.sender = None


class SupWebSocket(AppWebSocketEndpoint):
    encoding = "bytes"
    async def on_connect(self, websocket):
        await websocket.accept()
        # Registered only once the socket is open, and the snapshot is queued
        # before any broadcast can reach this client, so a batch of deltas can
        # never arrive ahead of the state it applies to.
        client = self.cli.register_client(websocket)
        log.debug("Sending indi init payload")
        client.send(orjson.dumps({
            'action': 'indi_init',
            'payload': self.cli.indi_client.to_serializable()['devices'],
        }))
        log.debug("Sending instgraph init payload")
        client.send(orjson.dumps({
            'action': 'instgraph_updated',
            'payload': self.cli.instgraph_state(),
        }))

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
        self.cli.unregister_client(websocket)

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
    """Watch the *directory* containing a single file and report changes to it.

    Watching the directory rather than the file itself is what makes atomic
    writes visible: a writer that does write-to-temp-then-rename never
    generates a modify event for the destination path, only a move (or a
    create, if the temp file lived elsewhere). An inode-level watch on the
    original file would also go deaf after the first replacement, since the
    inode it was watching is no longer the one at that path.

    Bursts are collapsed on the *trailing* edge: a rename is often preceded
    by create/modify events for the temp file, and the last event in a burst
    is the one that reflects the final contents.
    """
    def __init__(self, web_interface, file_path_to_watch, debouncing_interval_sec, loop):
        self.web_interface = web_interface
        self.file_path_to_watch = file_path_to_watch
        self.debouncing_interval_sec = debouncing_interval_sec
        self.loop = loop
        self._real_path_to_watch = os.path.realpath(file_path_to_watch)
        self._event_seq = 0

    def _paths_for(self, event):
        paths = [event.src_path]
        # Moves carry the destination separately; for an atomic replace that
        # destination is the only path that matches the file we care about.
        dest = getattr(event, 'dest_path', None)
        if dest:
            paths.append(dest)
        return paths

    def _matches(self, event):
        for path in self._paths_for(event):
            if isinstance(path, bytes):
                path = os.fsdecode(path)
            if os.path.realpath(path) == self._real_path_to_watch:
                return True
        return False

    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.event_type not in ('created', 'modified', 'moved', 'closed'):
            return
        if not self._matches(event):
            return

        self._event_seq += 1
        log.debug(f"Update noticed on target file ({event.event_type}): {event.src_path}")
        asyncio.run_coroutine_threadsafe(
            self._debounced_emit(self._event_seq),
            self.loop
        )

    async def _debounced_emit(self, seq):
        """Emit only if no further event arrived during the quiet interval."""
        try:
            await asyncio.sleep(self.debouncing_interval_sec)
            if seq != self._event_seq:
                return  # superseded by a later event in the same burst
            await self.web_interface.emit_instgraph_update()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning(f"Exception in _debounced_emit(): {type(e)=} {e}")

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
        help="How long the instGraph file must be quiet before telling clients over the websocket that it updated"
    )
    watch_retry_interval_sec : float = xconf.field(
        default=5.0,
        help="How long to wait before retrying when the directory holding the instGraph file does not exist yet"
    )
    instgraph_file_path : str = xconf.field(default=INSTGRAPH_FILE_PATH, help="Absolute path of .drawio file that instGraph updates")
    obs_root : str = xconf.field(default=OBS_ROOT, help="Root directory for observation file browsing")
    log_unit : str = xconf.field(default="lookyloo", help="systemd unit name whose journal to stream (empty to disable)")
    max_pending_updates_per_client : int = xconf.field(
        default=50,
        help="Updates that may queue for one websocket client before it is disconnected "
             "to resync (at the default batch interval, about ten seconds' worth)"
    )
    slow_send_warning_sec : float = xconf.field(
        default=1.0,
        help="Log a warning when sending one batch to one websocket client takes longer than this"
    )
    audible_alerts_device : str = xconf.field(
        default=AUDIBLE_ALERTS_DEVICE,
        help="INDI device whose playback events drive audible alerts in the browser (empty to disable)"
    )
    audible_alerts_cache_root : str = xconf.field(
        default=AUDIBLE_ALERTS_CACHE_ROOT,
        help="Directory the audible alerts device writes playback audio into"
    )

    def __post_init__(self):
        self._running_tasks = set()
        self._connected_clients = []
        self._last_instgraph_update = 0
        self._posix_instgraph_file_path = pathlib.Path(self.instgraph_file_path)
        self._last_instgraph_rev = None

    def register_client(self, websocket) -> WebSocketClient:
        client = WebSocketClient(
            websocket, self.max_pending_updates_per_client, self.slow_send_warning_sec
        )
        client.start()
        self._connected_clients.append(client)
        return client

    def unregister_client(self, websocket):
        for client in list(self._connected_clients):
            if client.websocket is websocket:
                self._connected_clients.remove(client)
                client.stop()

    def broadcast(self, payload: bytes):
        """Queue a payload for every connected client. Never waits on any of them."""
        for client in list(self._connected_clients):
            client.send(payload)

    async def emit_indi_updates(self):
        while True:
            try:
                batch = await self.indi_batcher.generate_batch()
                # Encoded once for everybody: the bytes are identical for
                # every client, and a busy instrument's batch is not cheap to
                # encode.
                payload = orjson.dumps({'action': 'indi_batch_update', 'payload': batch})
                self.broadcast(payload)
            except Exception as e:
                log.warning(f"Exception in emit_indi_updates(): {type(e)=} {e}")
                traceback.print_exc(file=sys.stdout)
            await asyncio.sleep(self.batch_update_interval_sec)

    def instgraph_state(self):
        """Identify the current contents of the instrument state graph file.

        The revision combines mtime, size, and inode. The inode matters:
        an atomic replace swaps in a different inode, so the revision changes
        even in the pathological case where the new file has the same size
        and a timestamp the filesystem can't distinguish from the old one.
        """
        rev = None
        try:
            st = self._posix_instgraph_file_path.stat()
            rev = f"{st.st_mtime_ns}-{st.st_size}-{st.st_ino}"
        except OSError as e:
            log.debug(f"Could not stat {self._posix_instgraph_file_path}: {e}")
        return {'file': self._posix_instgraph_file_path.name, 'rev': rev}

    async def emit_instgraph_update(self):
        """Send file update notification via WebSocket."""
        payload = self.instgraph_state()
        if payload['rev'] is None:
            log.debug("instgraph file is not readable, not notifying clients")
            return
        if payload['rev'] == self._last_instgraph_rev:
            log.debug(f"instgraph rev {payload['rev']} unchanged, not notifying clients")
            return
        self._last_instgraph_rev = payload['rev']
        log.debug(f"Sending instgraph update trigger for {payload['file']} rev {payload['rev']}")
        self.broadcast(orjson.dumps({'action': 'instgraph_updated', 'payload': payload}))

    async def start_file_watcher(self, file_path_to_watch=None):
        """Run the watchdog observer as an async background task."""
        loop = asyncio.get_running_loop()

        file_path_to_watch = pathlib.Path(file_path_to_watch or self._posix_instgraph_file_path)
        watch_dir = file_path_to_watch.parent

        # The containing directory has to exist before we can watch it, and it
        # may well not at startup. Wait for it rather than taking down the
        # whole task group (and with it the INDI client) on a bad path.
        while not watch_dir.is_dir():
            log.warning(f"Cannot watch {file_path_to_watch}: {watch_dir} does not exist, retrying")
            await asyncio.sleep(self.watch_retry_interval_sec)

        # Record the starting revision before the observer is live, so a
        # change landing during startup is still seen as a change rather than
        # being swallowed as the baseline.
        self._last_instgraph_rev = self.instgraph_state()['rev']

        event_handler = FileChangeHandler(self, file_path_to_watch, self.debouncing_interval_sec, loop)
        observer = observers.Observer()
        observer.schedule(event_handler, watch_dir.as_posix(), recursive=False)
        observer.start()
        log.info(f"Watching {watch_dir} for changes to {file_path_to_watch.name}")

        try:
            await asyncio.Event().wait()  # until cancelled at shutdown
        finally:
            observer.stop()
            await asyncio.to_thread(observer.join)

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
        for client in list(self._connected_clients):
            client.stop()
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
                Route('/audible-alerts/clip/{path:path}', endpoint=self.views.audible_alerts_clip),
                WebSocketRoute('/websocket', endpoint=partial(SupWebSocket, self)),
                WebSocketRoute('/ws/logs', endpoint=partial(LogStreamWebSocket, self)),
                Route(f"/{INSTGRAPH_DOWNLOAD_NAME}", endpoint=self.views.instgraph),
                Route('/{path:path}', endpoint=self.views.catch_all),
            ],
            lifespan=lifespan,
            middleware=[
                Middleware(GZipMiddleware),
                Middleware(CORSMiddleware, allow_origins=['*'])
            ]
        )
        uvicorn.run(self.app, host=self.bind_host, port=self.bind_port)
