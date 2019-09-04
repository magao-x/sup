import os.path
import sys
import uvloop
import asyncio
import logging
import socketio
from sanic.exceptions import NotFound
from sanic import Sanic
from sanic.response import raw, json, file
from pathlib import Path
from purepyindi.eventful import AsyncINDIClient
from purepyindi.constants import INDIPropertyKind, INDIActions, DEFAULT_HOST, DEFAULT_PORT
from purepyindi.generator import format_datetime_as_iso
from copy import deepcopy

def convert_indi_update_for_json(update):
    modified = deepcopy(update)
    # Convert Enums to strings
    modified['action'] = update['action'].value
    if 'kind' in update:
        modified['kind'] = update['kind'].value
    # Convert datetime to string ISO timestamp
    if 'timestamp' in update:
        modified['timestamp'] = format_datetime_as_iso(modified['timestamp'])
    if 'property' in update:
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
        if update['kind'] in (INDIPropertyKind.SWITCH, INDIPropertyKind.LIGHT):
            for key in update_prop['elements']:
                modified_prop['elements'][key] = update_prop['elements'][key]['value'].value
    return modified

static_folder_name = "static"
app = Sanic('sup')

sio = socketio.AsyncServer(async_mode='sanic')
sio.attach(app)

static_path = Path(__file__).parent / static_folder_name

app.config['SECRET_KEY'] = 'secret!'

@app.route('/api/properties')
async def api_properties(request):
    return raw(
        app.indi.to_json(),
        content_type='application/json',
    )

@app.route('/<path:path>')
async def catch_all(request, path):
    real_path = (static_path / path).resolve()
    print(real_path)
    if static_path in real_path.parents:  # prevent traversal vulnerability
        if real_path.exists():
            return await file(real_path)
    raise NotFound("No route or file at this URL")

@app.route('/')
async def index(request):
    return await file(static_path / 'index.html')

@sio.event
async def connect(sid, environ):
    print('connect ', sid)
    the_dict = app.indi.to_dict()
    print(the_dict)
    await sio.emit('indi_init', the_dict)

@sio.event
async def disconnect(sid):
    print('disconnect ', sid)

@sio.on('my event')
def handle_my_custom_event(sid, data):
    print('received json: ' + str(json))

async def relay_indi_updates(update):
    print("Got update", update)
    modified_update = convert_indi_update_for_json(update)
    if update['action'] == INDIActions.PROPERTY_DEF:
        await sio.emit('indi_def', modified_update)
    elif update['action'] == INDIActions.PROPERTY_SET:
        await sio.emit('indi_set', modified_update)
    elif update['action'] == INDIActions.PROPERTY_DEL:
        await sio.emit('indi_del', modified_update)
    else:
        print("Unknown update:", modified_update)

@app.listener('after_server_start')
async def init_connections(sanic, loop):
    logging.basicConfig(level=logging.DEBUG)
    sanic.indi = AsyncINDIClient('localhost', 7624)
    sanic.indi.add_async_watcher(relay_indi_updates)
    app.add_task(sanic.indi.run(reconnect_automatically=True))

@app.listener("before_server_stop")
async def close_connections(sanic, loop):
    await sanic.indi.stop()

def main(indi_host, indi_port):
    app.run(debug=True)

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
