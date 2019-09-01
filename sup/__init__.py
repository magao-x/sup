import os.path
import sys
import uvloop
import asyncio
import socketio
from sanic.exceptions import NotFound
from sanic import Sanic
from sanic.response import raw, json, file
from pathlib import Path
from purepyindi.eventful import AsyncINDIClient
from purepyindi.constants import INDIPropertyKind, INDIActions
from purepyindi.generator import format_datetime_as_iso
from copy import deepcopy

def convert_indi_update_for_json(update):
    modified = deepcopy(update)
    # Convert datetime to string ISO timestamp
    modified['timestamp'] = format_datetime_as_iso(modified['timestamp'])
    # Convert Enums to strings
    modified['action'] = update['action'].value
    modified['kind'] = update['kind'].value
    if 'perm' in update:
        modified['perm'] = update['perm'].value
    if 'state' in update:
        modified['state'] = update['state'].value
    if update['kind'] in (INDIPropertyKind.SWITCH, INDIPropertyKind.LIGHT):
        for idx, el in enumerate(update['elements']):
            modified['elements'][idx] = update['elements'][idx]['value'].value
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
    modified_update = convert_indi_update_for_json(update)
    if update['action'] == INDIActions.PROPERTY_DEF:
        await sio.emit('indi_def', modified_update)
    elif update['action'] == INDIActions.PROPERTY_SET:
        await sio.emit('indi_set', modified_update)
    elif update['action'] == INDIActions.PROPERTY_NEW:
        await sio.emit('indi_new', modified_update)
    elif update['action'] == INDIActions.PROPERTY_DEL:
        await sio.emit('indi_del', modified_update)
    else:
        print("Unknown update:", modified_update)

@app.listener('after_server_start')
async def init_connections(sanic, loop):
    sanic.indi = AsyncINDIClient('localhost', 7624)
    sanic.indi.add_async_watcher(relay_indi_updates)
    app.add_task(sanic.indi.run(reconnect_automatically=True))

@app.listener("before_server_stop")
async def close_connections(sanic, loop):
    await sanic.indi.stop()

def main():
    app.run(debug=True)

def console_entrypoint():
    sys.exit(main())

if __name__ == '__main__':
    console_entrypoint()
