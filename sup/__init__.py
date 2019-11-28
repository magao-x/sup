import os.path
import sys
import uvloop
import math
import asyncio
import logging
import json
import uvicorn
from pprint import pformat
import socketio
from starlette.exceptions import HTTPException
from starlette.applications import Starlette
from starlette.responses import UJSONResponse, FileResponse
from pathlib import Path
# from purepyindi import client
# from purepyindi.eventful import AsyncINDIClient
from purepyindi.constants import (
    INDIPropertyKind, INDIActions, DEFAULT_HOST, DEFAULT_PORT, parse_string_into_enum, SwitchState, ConnectionStatus
)
#     PropertyState
# )
# from purepyindi.generator import format_datetime_as_iso
# from purepyindi.parser import parse_iso_to_datetime
# import purepyindi.log
from .indi import BogusINDIClient, SupINDIClient
from copy import deepcopy
from .log import debug, info, warn, error, critical, set_log_level
import datetime
import pkg_resources

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
    __version__ = f.read().strip()

from collections.abc import MutableMapping, MutableSequence

BATCH_UPDATE_INTERVAL = 2 # second
PING_INTERVAL = 10

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

# def convert_indi_update_for_json(update):
#     modified = deepcopy(update)
#     # Convert Enums to strings
#     modified['action'] = update['action'].value
#     # Convert datetime to string ISO timestamp
#     if 'timestamp' in update:
#         modified['timestamp'] = format_datetime_as_iso(modified['timestamp'])
#     if 'property' in update:
#         modified['property']['kind'] = update['property']['kind'].value
#         update_prop = update['property']
#         modified_prop = modified['property']
#         modified_prop['timestamp'] = format_datetime_as_iso(modified_prop['timestamp'])
#         # Check for optional attrs
#         if 'perm' in update_prop:
#             modified_prop['perm'] = update_prop['perm'].value
#         if 'state' in update_prop:
#             modified_prop['state'] = update_prop['state'].value
#         if 'rule' in update_prop:
#             modified_prop['rule'] = update_prop['rule'].value
#         if update_prop['kind'] in (INDIPropertyKind.SWITCH, INDIPropertyKind.LIGHT):
#             for key in update_prop['elements']:
#                 modified_prop['elements'][key]['value'] = update_prop['elements'][key]['value'].value
#         if update_prop['kind'] is INDIPropertyKind.NUMBER:
#             for key in update_prop['elements']:
#                 the_value = update_prop['elements'][key]['value']
#                 modified_prop['elements'][key]['value'] = (
#                     the_value
#                     if the_value is not None and math.isfinite(the_value)
#                     else None
#                 )
#     return modified

static_folder_name = "static"
static_path = Path(__file__).parent / static_folder_name

sup_tasks = []


async def indi(request):
    # c = app.indi
    # for device in c.devices:
    #     d = c.devices[device]
    #     for prop in d.properties:
    #         p = d.properties[prop]
    #         for el in p.elements:
    #             e = p.elements[el]
    #             json(e.to_dict())
    # return response.raw(json.dumps(app.indi.to_jsonable(),  indent=4, sort_keys=True).encode('utf8'), headers={'Content-Type': 'application/json'})
    return UJSONResponse(request.app.indi.to_jsonable())

class NotFound(HTTPException):
    def __init__(self, *args, **kwargs):
        super().__init__(404, *args, **kwargs)

async def catch_all(request):
    path = request.path_params['path']
    real_path = (static_path / path).resolve()
    debug(f'catch_all caught path{real_path}')
    if static_path in real_path.parents:  # prevent traversal vulnerability
        if real_path.exists():
            return FileResponse(real_path.as_posix())
    else:
        warn(f'Attempted directory traversal with path {path}')
    raise NotFound("No route or file at this URL")


async def index(request):
    return FileResponse((static_path / 'index.html').as_posix())


sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*", # TODO only CORS in dev
    ping_interval=PING_INTERVAL,
)

@sio.event
async def connect(sid, environ):
    debug(f'socket.io client connected with sid: {sid}')
    the_dict = app.indi.to_jsonable()
    debug(f'sending current INDI state {pformat(the_dict)}')
    await sio.emit('indi_init', the_dict)

@sio.event
async def disconnect(sid):
    debug(f'socket.io client disconnected with sid: {sid}')

@sio.on('indi_new')
def handle_indi_new(sid, data):
    # if app.config.potemkin:
    #     print("Skipping indi_new because only fake data shown")
    #     return
    info(f"indi_new setting {data['device']}.{data['property']}.{data['element']}={data['value']}")
    prop = app.indi.devices[data['device']].properties[data['property']]
    if prop.KIND == INDIPropertyKind.NUMBER:
        prop.elements[data['element']].value = float(data['value'])
    elif prop.KIND == INDIPropertyKind.SWITCH:
        prop.elements[data['element']].value = parse_string_into_enum(data['value'], SwitchState)
    elif prop.KIND == INDIPropertyKind.TEXT:
        prop.elements[data['element']].value = data['value']

class INDIUpdateBatcher:
    def __init__(self, client_instance):
        self.client_instance = client_instance
        self.properties_to_update = set()
        self.properties_to_delete = set()
    async def process_update(self, update, *args, **kwargs):
        if update['action'] in (INDIActions.PROPERTY_SET, INDIActions.PROPERTY_DEF):
            device_name = update['device']
            property_name = update['property']['name']
            self.properties_to_update.add((device_name, property_name))
        elif update['action'] is INDIActions.PROPERTY_DEL:
            device_name = update['device']
            if 'name' in update:
                property_name = update['name']
                prop_to_del = (device_name, property_name)
            else:
                prop_to_del = (device_name, "*")
            self.properties_to_delete.add(prop_to_del)
    def _get_jsonable(self, device_name, property_name):
        return self.client_instance.devices[device_name].properties[property_name].to_jsonable()
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
            updates[f'{device_name}.{property_name}'] = self._get_jsonable(device_name, property_name)
        for device_name, property_name in self.properties_to_delete:
            deletions.append(f'{device_name}.{property_name}')

        batch = {
            'updates': updates,
            'deletions': deletions,
            'connected': self.client_instance.status == ConnectionStatus.CONNECTED,
        }
        self.properties_to_delete = set()
        self.properties_to_update = set()
        return batch

async def emit_updates():
    while True:
        batch = await app.indi_batcher.generate_batch()
        if batch is not None:
            await sio.emit('indi_batch_update', batch)
        await asyncio.sleep(BATCH_UPDATE_INTERVAL)

def make_indi_connection(potemkin=False):
    if potemkin:
        with open(Path(__file__).parent / 'demo_full_system_state.json', 'r') as f:
            initial_state = json.load(f)
        return BogusINDIClient(sio, initial_state)
    else:
        return SupINDIClient(sio, CONFIG['indi_host'], CONFIG['indi_port'])


CONFIG = {
    'indi_host': '127.0.0.1',
    'indi_port': 7624,
    'potemkin': False
}

def main(indi_host, indi_port, potemkin, bind_host, bind_port):
    global CONFIG
    logging.basicConfig(level='INFO')
    CONFIG['indi_host'] = indi_host
    CONFIG['indi_port'] = indi_port
    CONFIG['potemkin'] = potemkin
    # app.run(host=bind_host, port=bind_port)
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
        help=f"Specify hostname to connect to for INDI messages (default: {DEFAULT_HOST})",
        nargs="?",
        default=DEFAULT_HOST,
    )
    parser.add_argument(
        "-p", "--port",
        help=f"Specify port to connect to for INDI messages (default: {DEFAULT_PORT})",
        nargs="?",
        default=DEFAULT_PORT,
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
        default=8000,
    )
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        sys.exit(1)
    sys.exit(main(args.host, args.port, args.potemkin, args.bind_host, args.bind_port))

RUNNING_TASKS = set()

async def spawn_tasks():
    loop = asyncio.get_event_loop()
    app.indi = make_indi_connection(potemkin=CONFIG['potemkin'])
    app.indi_batcher = INDIUpdateBatcher(app.indi)
    app.indi.add_async_watcher(app.indi_batcher.process_update)
    app.update_queue = asyncio.Queue()
    indi_coro = app.indi.run(reconnect_automatically=True)
    RUNNING_TASKS.add(loop.create_task(indi_coro))
    if CONFIG['potemkin']:
        fiddling_coro = app.indi.fiddle_connection_status()
        RUNNING_TASKS.add(loop.create_task(fiddling_coro))
    emit_updates_coro = emit_updates()
    RUNNING_TASKS.add(loop.create_task(emit_updates_coro))

async def cancel_tasks():
    await app.indi.stop()
    for task in RUNNING_TASKS:
        task.cancel()

from starlette.routing import Route

app = Starlette(
    debug=True,
    routes=[
        Route('/', endpoint=index),
        Route('/indi', endpoint=indi),
        Route('/{path:path}', endpoint=catch_all)
    ],
    on_startup=[spawn_tasks],
    on_shutdown=[cancel_tasks],
)


app = socketio.ASGIApp(sio, app)

if __name__ == '__main__':
    console_entrypoint()
