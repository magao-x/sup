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

from collections.abc import MutableMapping, MutableSequence

BATCH_UPDATE_INTERVAL = 1 # second
PING_INTERVAL = 10

def merge_dicts(d1, d2):
    '''
    Merge dict keys and concatenate lists
    '''
    for k, v in d1.items():
        if k in d2:
            if isinstance(v, MutableMapping) and isinstance(d2[k], MutableMapping):
                d2[k] = merge_dicts(v, d2[k])
            elif isinstance(v, MutableSequence) and isinstance(d2[k], MutableSequence):
                d2[k] = v + d2[k]
    d3 = d1.copy()
    d3.update(d2)
    return d3

def utc_now():
    dt = datetime.datetime.utcnow()
    dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def log_updates(update):
    if 'property' in update:
        for elemname in update['property']['elements']:
            elem = update['property']['elements'][elemname]
            debug(f"{update['device']}.{update['property']['name']}.{elemname}={elem['value']} ({update['property']['state'].value})")
    else:
        debug(update)

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
    c = app.indi
    for device in c.devices:
        d = c.devices[device]
        for prop in d.properties:
            p = d.properties[prop]
            for el in p.elements:
                e = p.elements[el]
                json(e.to_dict())
    return json(app.indi.to_dict())

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
    the_dict = app.indi.to_dict()
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

async def relay_indi_updates(update):
    await app.update_queue.put(convert_indi_update_for_json(update))

async def emit_updates():
    while True:
        if not app.update_queue.empty():
            updates = {'indi_updates': []}
            while not app.update_queue.empty():
                updates['indi_updates'].append(app.update_queue.get_nowait())
            await sio.emit('indi_batch_update', updates)
        await asyncio.sleep(BATCH_UPDATE_INTERVAL)

@app.listener('after_server_start')
async def init_connections(sanic, loop):
    purepyindi.log.set_log_level('INFO')
    app.indi = AsyncINDIClient(app.config.indi_host, app.config.indi_port)
    app.indi.add_async_watcher(relay_indi_updates)
    app.update_queue = asyncio.Queue()
    app.indi.add_watcher(log_updates)
    app.add_task(app.indi.run(reconnect_automatically=True))
    app.add_task(emit_updates())

@app.listener("before_server_stop")
async def close_connections(sanic, loop):
    await sanic.indi.stop()

def main(indi_host, indi_port):
    logging.basicConfig(level='WARN')
    app.config.indi_host = indi_host
    app.config.indi_port = indi_port
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
    sys.exit(main(args.host, args.port))

if __name__ == '__main__':
    console_entrypoint()
