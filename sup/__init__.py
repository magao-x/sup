import os.path
import sys
import uvloop
import math
import asyncio
import logging
from pprint import pformat
import socketio
from sanic.exceptions import NotFound
from sanic import Sanic
from sanic.response import raw, json, file
from pathlib import Path
from purepyindi.eventful import AsyncINDIClient
from purepyindi.constants import INDIPropertyKind, INDIActions, DEFAULT_HOST, DEFAULT_PORT, parse_string_into_enum, SwitchState
from purepyindi.generator import format_datetime_as_iso
import purepyindi.log
from copy import deepcopy
from .log import debug, info, warn, error, critical, set_log_level
import datetime
import jsonpatch

from collections.abc import MutableMapping, MutableSequence

BATCH_UPDATE_INTERVAL = 1 # second
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

def convert_indi_update_for_json(update):
    modified = deepcopy(update)
    # Convert Enums to strings
    modified['action'] = update['action'].value
    # Convert datetime to string ISO timestamp
    if 'timestamp' in update:
        modified['timestamp'] = format_datetime_as_iso(modified['timestamp'])
    if 'property' in update:
        modified['property']['kind'] = update['property']['kind'].value
        update_prop = update['property']
        modified_prop = modified['property']
        modified_prop['timestamp'] = format_datetime_as_iso(modified_prop['timestamp'])
        # Check for optional attrs
        if 'perm' in update_prop:
            modified_prop['perm'] = update_prop['perm'].value
        if 'state' in update_prop:
            modified_prop['state'] = update_prop['state'].value
        if 'rule' in update_prop:
            modified_prop['rule'] = update_prop['rule'].value
        if update_prop['kind'] in (INDIPropertyKind.SWITCH, INDIPropertyKind.LIGHT):
            for key in update_prop['elements']:
                modified_prop['elements'][key]['value'] = update_prop['elements'][key]['value'].value
        if update_prop['kind'] is INDIPropertyKind.NUMBER:
            for key in update_prop['elements']:
                the_value = update_prop['elements'][key]['value']
                modified_prop['elements'][key]['value'] = (
                    the_value
                    if the_value is not None and math.isfinite(the_value)
                    else None
                )
    return modified

static_folder_name = "static"
app = Sanic('sup')


sio = socketio.AsyncServer(
    async_mode='sanic',
    cors_allowed_origins="*", # TODO only CORS in dev
    ping_interval=PING_INTERVAL,
)
sio.attach(app)

static_path = Path(__file__).parent / static_folder_name

app.config['SECRET_KEY'] = 'secret!'

@app.route('/indi')
async def indi(request):
    # c = app.indi
    # for device in c.devices:
    #     d = c.devices[device]
    #     for prop in d.properties:
    #         p = d.properties[prop]
    #         for el in p.elements:
    #             e = p.elements[el]
    #             json(e.to_dict())
    return json(app.indi.to_jsonable())

@app.route('/<path:path>')
async def catch_all(request, path):
    real_path = (static_path / path).resolve()
    debug(f'catch_all caught path{real_path}')
    if static_path in real_path.parents:  # prevent traversal vulnerability
        if real_path.exists():
            return await file(real_path)
    else:
        warn(f'Attempted directory traversal with path {path}')
    raise NotFound("No route or file at this URL")

@app.route('/')
async def index(request):
    return await file(static_path / 'index.html')

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
    async def process_update(self, update, *_):
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
    async def _get_jsonable(self, device_name, property_name):
        return self.client_instance.devices[device_name].properties[property_name].to_jsonable()
    async def generate_batch(self):
        updates = {}
        deletions = []

        updated_not_deleted = self.properties_to_update - self.properties_to_delete
        for device_name, property_name in updated_not_deleted:
            updates[f'{device_name}.{property_name}'] = await self._get_jsonable(device_name, property_name)
        for device_name, property_name in self.properties_to_delete:
            deletions.append(f'{device_name}.{property_name}')
        
        batch = {
            'updates': updates,
            'deletions': deletions,
        }
        self.properties_to_delete = set()
        self.properties_to_update = set()
        return batch

async def emit_updates():
    while True:
        await sio.emit('indi_batch_update', await app.indi_batcher.generate_batch())
        await asyncio.sleep(BATCH_UPDATE_INTERVAL)

@app.listener('after_server_start')
async def init_connections(sanic, loop):
    app.indi = AsyncINDIClient(app.config.indi_host, app.config.indi_port)
    app.indi_batcher = INDIUpdateBatcher(app.indi)
    app.indi.add_async_watcher(app.indi_batcher.process_update)
    app.update_queue = asyncio.Queue()
    app.indi.add_watcher(log_updates)
    app.add_task(app.indi.run(reconnect_automatically=True))
    app.add_task(emit_updates())

@app.listener("before_server_stop")
async def close_connections(sanic, loop):
    await sanic.indi.stop()

def main(indi_host, indi_port, indi_read_only):
    logging.basicConfig(level='WARN')
    # log = logging.getLogger('purepyindi.eventful')
    # log.setLevel('DEBUG')
    app.config.indi_host = indi_host
    app.config.indi_port = indi_port
    app.config.indi_read_only = indi_read_only
    app.run()

def console_entrypoint():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--help",
        help="show this help message and exit",
        action="store_true",
    )
    parser.add_argument(
        "--read-only",
        help="Prevent requests to set new values from being sent to the INDI server",
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
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        sys.exit(1)
    sys.exit(main(args.host, args.port, args.read_only))

if __name__ == '__main__':
    console_entrypoint()
