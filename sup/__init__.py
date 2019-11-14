import os.path
import sys
import uvloop
import math
import asyncio
import logging
import json
from pprint import pformat
import socketio
from sanic.exceptions import NotFound
from sanic import Sanic
from sanic import response
from pathlib import Path
from purepyindi import client
from purepyindi.eventful import AsyncINDIClient
from purepyindi.constants import (
    INDIPropertyKind, INDIActions, DEFAULT_HOST, DEFAULT_PORT, parse_string_into_enum, SwitchState,
    PropertyState
)
from purepyindi.generator import format_datetime_as_iso
from purepyindi.parser import parse_iso_to_datetime
import purepyindi.log
from copy import deepcopy
from .log import debug, info, warn, error, critical, set_log_level
import datetime
import pkg_resources

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
    __version__ = f.read().strip()

from collections.abc import MutableMapping, MutableSequence

BATCH_UPDATE_INTERVAL = 1 # second
PING_INTERVAL = 10

def property_from_jsonable(jsonable):
    jsonable['timestamp'] = parse_iso_to_datetime(jsonable['timestamp'])
    jsonable['_perm'] = parse_string_into_enum(jsonable.pop('perm'), client.PropertyPerm)
    jsonable['_state'] = parse_string_into_enum(jsonable.pop('state'), client.PropertyState)
    jsonable['_label'] = jsonable.pop('label', None)
    jsonable['kind'] = parse_string_into_enum(jsonable['kind'], client.INDIPropertyKind)
    if jsonable['kind'] is INDIPropertyKind.SWITCH:
        jsonable['rule'] = parse_string_into_enum(jsonable.get('rule', 'OneOfMany'), client.SwitchRule)
    return jsonable

def element_from_jsonable(jsonable, kind):
    if kind is INDIPropertyKind.SWITCH:
        jsonable['_value'] = parse_string_into_enum(jsonable.pop('value'), client.SwitchState)
    elif kind is INDIPropertyKind.LIGHT:
        jsonable['_value'] = parse_string_into_enum(jsonable.pop('value'), client.PropertyState)
    else:
        jsonable['_value'] = jsonable.pop('value')
    jsonable['_label'] = jsonable.pop('label', None)
    return jsonable

class BogusINDIClient(AsyncINDIClient):
    KIND_TO_CLASSES = {
        'num': (client.NumberProperty, client.NumberElement),
        'txt': (client.TextProperty, client.TextElement),
        'swt': (client.SwitchProperty, client.SwitchElement),
        'lgt': (client.LightProperty, client.LightElement),
    }
    def __init__(self, initial_state):
        super().__init__(host=None, port=None)
        for key in initial_state:
            device_state = initial_state[key]
            dev = self.get_or_create_device(key)
            for property_name in device_state['properties']:
                property_state = device_state['properties'][property_name]
                PROP_CLASS, ELT_CLASS = self.KIND_TO_CLASSES[property_state['kind']]
                dev.properties[property_name] = prop = PROP_CLASS(property_name, dev)
                property_state['_label'] = property_state.pop('label')
                elements = property_state.pop('elements')
                property_state = property_from_jsonable(property_state)
                for prop_key in property_state:
                    setattr(prop, prop_key, property_state[prop_key])
                for element_name in elements:
                    prop.elements[element_name] = elt = ELT_CLASS(element_name, prop)
                    history_state = elements[element_name].pop('history')
                    elt.history.times = list(map(parse_iso_to_datetime, history_state['times']))
                    if PROP_CLASS.KIND is INDIPropertyKind.SWITCH:
                        elt.history.values = [
                            parse_string_into_enum(val, client.SwitchState)
                            for val in history_state['values']
                        ]
                    elif PROP_CLASS.KIND is INDIPropertyKind.LIGHT:
                        elt.history.values = [
                            parse_string_into_enum(val, client.PropertyState)
                            for val in history_state['values']
                        ]
                    else:
                        elt.history.values = history_state['values']
                    element_state = element_from_jsonable(elements[element_name], PROP_CLASS.KIND)
                    for elt_key in element_state:
                        setattr(elt, elt_key, element_state[elt_key])
    def mutate(self, update):
        dev, prop = update['device'], update['property']['name']
        prop = self.devices[dev].properties[prop]
        original_state = prop._state
        self.apply_update(update)
        async def clear_busy():
            update['action'] = INDIActions.PROPERTY_SET
            update['property']['state'] = original_state
            await asyncio.sleep(2)
            self.apply_update(update)
        asyncio.create_task(clear_busy)

    async def run(self, *args, **kwargs):
        return

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

sup_tasks = []

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
    return response.raw(json.dumps(app.indi.to_jsonable(),  indent=4, sort_keys=True).encode('utf8'), headers={'Content-Type': 'application/json'})

@app.route('/<path:path>')
async def catch_all(request, path):
    real_path = (static_path / path).resolve()
    debug(f'catch_all caught path{real_path}')
    if static_path in real_path.parents:  # prevent traversal vulnerability
        if real_path.exists():
            return await response.file(real_path)
    else:
        warn(f'Attempted directory traversal with path {path}')
    raise NotFound("No route or file at this URL")

@app.route('/')
async def index(request):
    return await response.file(static_path / 'index.html')

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
    if app.config.potemkin:
        print("Skipping indi_new because only fake data shown")
        return
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

def make_indi_connection(potemkin):
    if potemkin:
        # with open(Path(__file__).parent.parent / 'full_system_props.json', 'r') as f:
        #     initial_state = json.load(f)
        # return BogusINDIClient(initial_state)
        raise NotImplementedError("TODO")
    else:
        return AsyncINDIClient(app.config.indi_host, app.config.indi_port)

@app.listener('after_server_start')
async def init_connections(sanic, loop):
    app.indi = make_indi_connection(app.config.potemkin)
    app.indi_batcher = INDIUpdateBatcher(app.indi)
    app.indi.add_async_watcher(app.indi_batcher.process_update)
    app.update_queue = asyncio.Queue()
    # app.indi.add_watcher(log_updates)
    indi_coro = app.indi.run(reconnect_automatically=True)
    sup_tasks.append(loop.create_task(indi_coro))
    emit_updates_coro = emit_updates()
    sup_tasks.append(loop.create_task(emit_updates_coro))

@app.listener("before_server_stop")
async def close_connections(sanic, loop):
    await sanic.indi.stop()
    for task in sup_tasks:
        task.cancel()

def main(indi_host, indi_port, potemkin, bind_host, bind_port):
    logging.basicConfig(level='INFO')
    app.config.indi_host = indi_host
    app.config.indi_port = indi_port
    app.config.potemkin = potemkin
    app.run(host=bind_host, port=bind_port)

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

if __name__ == '__main__':
    console_entrypoint()
