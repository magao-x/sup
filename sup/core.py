from functools import partial
import pathlib
import traceback
import asyncio
import datetime
import logging
import os
import os.path
import sys
from pathlib import Path

import xconf
from starlette.endpoints import WebSocketEndpoint
import numpy as np
import matplotlib
matplotlib.use('Agg')
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
from starlette.routing import Route, WebSocketRoute

from .constants import (
    INSTRUMENT_CONFIG_ROOT, InstrumentLayouts, SITE_LOCATION,
    CONFIG_FILENAME,
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
        return OrjsonResponse(request.app.indi.to_serializable()['devices'])

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

    async def demo(self, request):
        return FileResponse((static_path / 'demo.html').as_posix())

    async def config(self, request):
        config = xconf.config_to_dict(self.app)
        return OrjsonResponse(config)

    async def airmass(self, request):
        ra_str, dec_str = request.query_params.get('ra', None), request.query_params.get('dec', None)
        if ra_str is None or dec_str is None:
            raise HTTPException(400)
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
        return OrjsonResponse(payload)

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
    def __init__(self, app : 'WebInterface', *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.app = app

class SupWebSocket(AppWebSocketEndpoint):
    encoding = "bytes"
    async def on_connect(self, websocket):
        self.app._connected_clients.append(websocket)
        await websocket.accept()
        await websocket.send_bytes(orjson.dumps({
            'action': 'init',
            'payload': self.app.indi_client.to_serializable()['devices'],
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
            self.app.indi_client[f"{payload['device']}.{payload['property']}.{payload['element']}"] = value
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
            idx = self.app._connected_clients.index(websocket)
            self.app._connected_clients.pop(idx)
        except ValueError:
            pass

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
    indi : IndiConfig = xconf.field(default=IndiConfig())
    potemkin : bool = xconf.field(
        default=False,
        help="Whether to load a system snapshot for testing (disables connection to INDI server)"
    )
    debug_mode : bool = xconf.field(default=True, help="Initialize Starlette framework in debug mode")
    batch_update_interval_sec : float = xconf.field(
        default=0.2,
        help="How often to emit a batch of updates over the websocket to connected clients"
    )

    def __post_init__(self):
        self._running_tasks = set()
        self._connected_clients = []

    async def emit_updates(self):
        while True:
            try:
                batch = await self.indi_batcher.generate_batch()
                for websocket in self._connected_clients:
                    try:
                        await websocket.send_bytes(orjson.dumps({'action': 'batch_update', 'payload': batch}))
                    except Exception as e:
                        log.debug(f"Swallowed exception in websocket.send_bytes: {type(e)} {e}")
            except Exception as e:
                log.warning(f"Exception in emit_updates(): {type(e)=} {e}")
                traceback.print_exc(file=sys.stdout)
            await asyncio.sleep(self.batch_update_interval_sec)

    async def trigger_get_properties(self, message):
        if message is constants.ConnectionStatus.CONNECTED:
            log.debug(f"Trigger get properties: {message}")
            self.indi_client.get_properties()

    async def spawn_tasks(self):
        loop = asyncio.get_event_loop()
        conn = purepyindi2.AsyncIndiTcpConnection(host=self.indi.hostname, port=self.indi.port)
        self.indi_client = purepyindi2.IndiClient(conn)
        loop.create_task(self.indi_client.connection.add_async_callback(constants.TransportEvent.connection, self.trigger_get_properties))

        self.indi_batcher = INDIUpdateBatcher(self.indi_client)
        loop.create_task(self.indi_client.connection.add_async_callback(constants.TransportEvent.inbound, self.indi_batcher.process_update))

        indi_coro = self.indi_client.connection.run(reconnect_automatically=True)
        self._running_tasks.add(loop.create_task(indi_coro))

        emit_updates_coro = self.emit_updates()
        self._running_tasks.add(loop.create_task(emit_updates_coro))

    async def cancel_tasks(self):
        await self.indi_client.connection.stop()
        for task in self._running_tasks:
            task.cancel()

    def main(self):
        self.views = SupViews(self)
        self.app = Starlette(
            debug=self.debug_mode,
            routes=[
                Route('/', endpoint=self.views.index),
                Route('/indi', endpoint=self.views.indi),
                Route('/light-path', endpoint=self.views.light_path),
                Route('/demo', endpoint=self.views.demo),
                Route('/airmass', endpoint=self.views.airmass),
                Route('/config', endpoint=self.views.config),
                WebSocketRoute('/websocket', endpoint=partial(SupWebSocket, self)),
                Route('/{path:path}', endpoint=self.views.catch_all),
            ],
            on_startup=[self.spawn_tasks],
            on_shutdown=[self.cancel_tasks],
            middleware=[
                Middleware(GZipMiddleware),
                Middleware(CORSMiddleware, allow_origins=['*'])
            ]
        )
        uvicorn.run(self.app, host=self.bind_host, port=self.bind_port)
