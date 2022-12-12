from io import BytesIO
import traceback
# from starlette.websockets import WebSocket
from starlette.endpoints import WebSocketEndpoint
import numpy as np
import matplotlib
from astroplan.plots import dark_style_sheet
from astropy.coordinates import SkyCoord

matplotlib.use('Agg')
import asyncio
import datetime
import logging
import math
import os
import os.path
import sys
from copy import deepcopy
from pathlib import Path
from pprint import pformat
import websockets

import aiohttp
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
from starlette.responses import FileResponse, StreamingResponse
from starlette.routing import Route, WebSocketRoute

# from .indi import BogusINDIClient, SupINDIClient
from .log import critical, debug, error, info, set_log_level, warn

log = logging.getLogger(__name__)

from .utils import OrjsonResponse

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
    __version__ = f.read().strip()

from collections.abc import MutableMapping, MutableSequence

LCO_COORDINATES = EarthLocation.of_site('Las Campanas Observatory')
BATCH_UPDATE_INTERVAL = 0.2 # second
PING_INTERVAL = 10
MAGAOX_ROLE = os.environ.get('MAGAOX_ROLE', 'workstation')
import pathlib

MAGAOX_CONFIG_PATH = pathlib.Path("/opt/MagAOX/config")

async def light_path(request):
    light_path_config = MAGAOX_CONFIG_PATH / 'light_path.toml'
    if not light_path_config.exists():
        light_path_config = Path(__file__).parent / 'light_path_ex.toml'
    
    with open(light_path_config) as fh:
        light_path_dict = toml.loads(fh.read())
    return OrjsonResponse(light_path_dict)

def utc_now():
    dt = datetime.datetime.utcnow()
    dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def log_updates(update, did_anything_change):
    if 'property' in update:
        for elemname in update['property']['elements']:
            elem = update['property']['elements'][elemname]
            if did_anything_change:
                print(f"{update['device']}.{update['property']['name']}.{elemname}={elem['value']} ({update['property']['state'].value})")

static_folder_name = "static"
static_path = (Path(__file__).parent / static_folder_name).resolve()

sup_tasks = []


async def indi(request):
    return OrjsonResponse(request.app.indi.to_serializable()['devices'])

class NotFound(HTTPException):
    def __init__(self, *args, **kwargs):
        super().__init__(404, *args, **kwargs)

async def catch_all(request):
    path = request.path_params['path']
    real_path = (static_path / path).resolve()
    print(f'catch_all caught path {real_path}, looking for {static_path=} in {list(real_path.parents)=}')
    
    if static_path in real_path.parents:  # prevent traversal vulnerability
        if real_path.exists():
            return FileResponse(real_path.as_posix())
    else:
        warn(f'Attempted directory traversal with path {path}')
    raise NotFound("No route or file at this URL")


async def index(request):
    return FileResponse((static_path / 'index.html').as_posix())

async def demo(request):
    return FileResponse((static_path / 'demo.html').as_posix())



LCO_SITE = Observer.at_site('Las Campanas Observatory')

async def airmass(request):
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

async def emit_updates():
    while True:
        try:
            batch = await app.indi_batcher.generate_batch()
            for websocket in connected_clients:
                try:
                    await websocket.send_bytes(orjson.dumps({'action': 'batch_update', 'payload': batch}))
                except Exception as e:
                    log.debug(f"Swallowed exception in websocket.send_bytes: {type(e)} {e}")
        except Exception as e:
            log.warning(f"Exception in emit_updates(): {type(e)=} {e}")
            traceback.print_exc(file=sys.stdout)
        await asyncio.sleep(BATCH_UPDATE_INTERVAL)

CONFIG = {
    'indi_host': '127.0.0.1',
    'indi_port': 7624,
    'potemkin': False
}

def main(indi_host, indi_port, potemkin, bind_host, bind_port):
    global CONFIG
    logging.basicConfig(level='WARN')
    CONFIG['indi_host'] = indi_host
    CONFIG['indi_port'] = indi_port
    CONFIG['potemkin'] = potemkin
    log.setLevel('DEBUG')
    uvicorn.run(app, host=bind_host, port=bind_port)

def console_entrypoint():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--help",
        help="show this help message and exit",
        action="store_true",
    )
    parser.add_argument(
        "--potemkin",
        help="A potemkin instrument (no real instrument connection)",
        action="store_true",
    )
    parser.add_argument(
        "-h", "--host",
        help=f"Specify hostname to connect to for INDI messages (default: {constants.DEFAULT_HOST})",
        nargs="?",
        default=constants.DEFAULT_HOST,
    )
    parser.add_argument(
        "-p", "--port",
        help=f"Specify port to connect to for INDI messages (default: {constants.DEFAULT_PORT})",
        nargs="?",
        type=int,
        default=constants.DEFAULT_PORT,
    )
    parser.add_argument(
        "-b", "--bind-host",
        help="Specify hostname or IP to bind web server to (default: 127.0.0.1)",
        nargs="?",
        default="127.0.0.1",
    )
    parser.add_argument(
        "-n", "--bind-port",
        help="Specify port to bind web server to (default: 8000)",
        nargs="?",
        type=int,
        default=8000,
    )
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        sys.exit(1)
    sys.exit(main(args.host, args.port, args.potemkin, args.bind_host, args.bind_port))


def orjson_to_utf8(obj):
    buf = orjson.dumps(obj)
    return buf.decode('utf8')

RUNNING_TASKS = set()

async def trigger_get_properties(message):
    log.debug(f"Trigger get properties: {message}")
    app.indi.get_properties()

async def spawn_tasks():
    loop = asyncio.get_event_loop()
    conn = purepyindi2.AsyncIndiTcpConnection(host=CONFIG['indi_host'], port=CONFIG['indi_port'])
    app.indi = purepyindi2.IndiClient(conn)
    loop.create_task(conn.add_async_callback(constants.TransportEvent.connection, trigger_get_properties))

    app.indi_batcher = INDIUpdateBatcher(app.indi)
    loop.create_task(conn.add_async_callback(constants.TransportEvent.inbound, app.indi_batcher.process_update))

    indi_coro = app.indi.connection.run()
    RUNNING_TASKS.add(loop.create_task(indi_coro))

    emit_updates_coro = emit_updates()
    RUNNING_TASKS.add(loop.create_task(emit_updates_coro))

async def cancel_tasks():
    await app.indi.connection.stop()
    for task in RUNNING_TASKS:
        task.cancel()

connected_clients = []

class SupWebSocket(WebSocketEndpoint):
    encoding = "bytes"
    async def on_connect(self, websocket):
        connected_clients.append(websocket)
        await websocket.accept()
        await websocket.send_bytes(orjson.dumps({
            'action': 'init',
            'payload': app.indi.to_serializable()['devices'],
        }))

    async def on_receive(self, websocket, data):
        data_obj = orjson.loads(data)
        log.debug(f"Recv from {websocket.client.host}: {data_obj}")
        if data_obj.get('action') == 'indi_new':
            payload = data_obj['payload']
            if not (
                'device' in payload and
                'property' in payload and
                'element' in payload and
                'value' in payload
            ):
                log.error("Received invalid message: {data_obj}")
                return
            try:
                app.indi[f"{payload['device']}.{payload['property']}.{payload['element']}"] = payload['value']
            except Exception as e:
                log.exception(f"Swallowed exception: Couldn't set INDI value from {payload}")


    async def on_disconnect(self, websocket, close_code):
        try:
            idx = connected_clients.index(websocket)
            connected_clients.pop(idx)
        except ValueError:
            pass

app = Starlette(
    debug=True,
    routes=[
        Route('/', endpoint=index),
        Route('/indi', endpoint=indi),
        Route('/light-path', endpoint=light_path),
        Route('/demo', endpoint=demo),
        Route('/airmass', endpoint=airmass),
        # Mount('/video', routes=video.ROUTES),
        WebSocketRoute('/websocket', endpoint=SupWebSocket),
        Route('/{path:path}', endpoint=catch_all),
    ],
    on_startup=[spawn_tasks],
    on_shutdown=[cancel_tasks],
    middleware=[
        Middleware(GZipMiddleware),
        Middleware(CORSMiddleware, allow_origins=['*'])
    ]
)


logging.basicConfig(level='WARN')
log.setLevel(os.environ.get('SUP_LOG_LEVEL', 'DEBUG'))

if __name__ == '__main__':
    console_entrypoint()
