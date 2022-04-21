from io import BytesIO

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

import aiohttp
import astropy.units as u
import matplotlib.pyplot as plt
import orjson
import pkg_resources
import socketio
import toml
import uvicorn
import uvloop
from astroplan import FixedTarget, Observer
from astroplan.plots import plot_airmass, plot_parallactic
from astropy.coordinates import EarthLocation
from astropy.time import Time
from purepyindi.constants import (DEFAULT_HOST, DEFAULT_PORT, ConnectionStatus,
                                  INDIActions, INDIPropertyKind, SwitchState,
                                  parse_string_into_enum)
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import FileResponse, StreamingResponse
from starlette.routing import Mount, Route

from .indi import BogusINDIClient, SupINDIClient
from .log import critical, debug, error, info, set_log_level, warn
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
    return OrjsonResponse(request.app.indi.to_jsonable())

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
    
    
    # with plt.style.context('dark_background'):
    #     fig, (airmass_ax, parang_ax) = plt.subplots(ncols=2, figsize=(6, 6))
    #     plot_airmass(
    #         target,
    #         LCO_SITE,
    #         current_time,
    #         # altitude_yaxis=True,
    #         ax=airmass_ax,
    #         brightness_shading=True,
    #         style_sheet=dark_style_sheet,
    #     )
    #     airmass_ax.grid(True)
    #     plot_parallactic(
    #         target,
    #         LCO_SITE,
    #         current_time,
    #         ax=parang_ax,
    #         style_sheet=dark_style_sheet,
    #     )
    #     plt.tight_layout()
    #     fig.savefig(buf, dpi=300)
    # buf.seek(0)
    # return StreamingResponse(buf, media_type='image/png')
    

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*", # TODO only CORS in dev
    ping_interval=PING_INTERVAL,
    # engineio_logger=True,
    # logger=True,
)

@sio.event
async def connect(sid, environ):
    debug(f'socket.io client connected with sid: {sid}')
    await sio.emit('indi_init', app.indi.to_jsonable(), room=sid)

@sio.event
async def disconnect(sid):
    debug(f'socket.io client disconnected with sid: {sid}')

@sio.on('indi_new')
def handle_indi_new(sid, data):
    info(f"indi_new setting {data['device']}.{data['property']}.{data['element']}={data['value']}")
    prop = app.indi.devices[data['device']].properties[data['property']]
    try:
        if prop.KIND == INDIPropertyKind.NUMBER:
            prop.elements[data['element']].value = float(data['value'])
        elif prop.KIND == INDIPropertyKind.SWITCH:
            prop.elements[data['element']].value = parse_string_into_enum(data['value'], SwitchState)
        elif prop.KIND == INDIPropertyKind.TEXT:
            prop.elements[data['element']].value = data['value']
    except ValueError:
        pass

class INDIStateTransitionNotifier:
    def __init__(self, client_instance):
        self._elements_watched = {}
        self._element_checks = {}
        self._element_notifiers = {}
        self.client_instance = client_instance
    async def add_notifier(self, indi_id, handler):
        async def notifier_closure():
            previous_value = self._elements_watched.get(indi_id)
            current_value = self.client_instance[indi_id]
            if current_value != previous_value:
                await handler(indi_id, current_value)
                self._elements_watched[indi_id] = current_value
        self._element_notifiers[indi_id] = notifier_closure
        self._elements_watched[indi_id] = None
    async def trigger_notifier(self, indi_id):
        if indi_id in self._element_notifiers:
            await self._element_notifiers[indi_id]()
    async def add_transition(self, indi_id, was, now, handler):
        async def transition_closure():
            previous_value = self._elements_watched.get(indi_id)
            if previous_value == was:
                await handler(indi_id, previous_value, now)
                self._elements_watched[indi_id] = now
        self._element_checks[(indi_id, now)] = transition_closure
        self._elements_watched[indi_id] = None
    async def trigger_transition(self, indi_id, current_value):
        if (indi_id, current_value) in self._element_checks:
            await self._element_checks[(indi_id, current_value)]()
    async def process_update(self, update, *_, **__):
        if update['action'] is INDIActions.PROPERTY_SET:
            device_name = update['device']
            property_name = update['property']['name']
            for elt in update['property']['elements'].values():
                indi_id = f"{device_name}.{property_name}.{elt['name']}"
                if indi_id in self._elements_watched:
                    new_value = elt['value']
                    # Fire any matching state-transition handler
                    await self.trigger_notifier(indi_id)
                    # Fire any matching notification handler
                    await self.trigger_transition(indi_id, new_value)
                    # Update _elements_watched with current value
                    self._elements_watched[indi_id] = new_value

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
            try:
                updates[f'{device_name}.{property_name}'] = self._get_jsonable(device_name, property_name)
            except KeyError:
                # race condition where device or property can be deleted
                # before the batch gets sent
                continue
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
        try:
            batch = await app.indi_batcher.generate_batch()
            if batch is not None:
                await sio.emit('indi_batch_update', batch)
        except Exception as e:
            print(f"Exception in emit_updates(): {type(e)=} {e}")
        await asyncio.sleep(BATCH_UPDATE_INTERVAL)

def make_indi_connection(potemkin=False):
    if potemkin:
        with open(Path(__file__).parent / 'demo_full_system_state.json', 'r') as f:
            initial_state = orjson.loads(f.read())
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
    logging.basicConfig(level='WARN')
    CONFIG['indi_host'] = indi_host
    CONFIG['indi_port'] = indi_port
    CONFIG['potemkin'] = potemkin
    uvicorn.run(wrapped_app, host=bind_host, port=bind_port)

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


def orjson_to_utf8(obj):
    buf = orjson.dumps(obj)
    return buf.decode('utf8')

RUNNING_TASKS = set()
VIZZY_API_URL = 'https://vizzy.xwcl.science/api/magao-x/events'
async def vizzy_relay(message_queue):
    async with aiohttp.ClientSession(json_serialize=orjson_to_utf8) as session:
        while True:
            msgdict = await message_queue.get()
            print(f'vizzy_relay: got {msgdict}')
            if app.state.should_notify:
                async with session.post(VIZZY_API_URL, json=msgdict) as resp:
                    print(resp.status)
                    print(await resp.json())

last_pointing_announced = None

async def register_onsky(indi_client, indi_notifier, vizzy_queue):
    print("Registering stuff for real ops")
    not_real_stars = set(('none', 'Pointing'))
    async def pointing_changes(indi_id, catalog_name):
        global last_pointing_announced
        if catalog_name == 'UNKNOWN' or catalog_name in not_real_stars:
            return
        simbad_search_url = f"http://simbad.u-strasbg.fr/simbad/sim-id?Ident={catalog_name}&NbIdent=1&Radius=2&Radius.unit=arcmin&submit=submit+id"
        msgdict = {
            'message': f'Pointing at <{simbad_search_url}|{catalog_name}>',
            'channel': '#observing',
        }
        print(msgdict)
        if catalog_name != last_pointing_announced:
            await vizzy_queue.put(msgdict)
            last_pointing_announced = catalog_name
    await indi_notifier.add_notifier(
        'tcsi.catalog.object',
        handler=pointing_changes
    )
    # async def on_sky_loop_changes(indi_id, current_value):
    #     if indi_client['pdu0.source.state'] == 'On' or indi_client['stagepickoff.presetName.in'] == SwitchState.ON:
    #         return
    #     try:
    #         target_message = f" on {indi_client['tcsi.catalog.object']}"
    #     except KeyError:
    #         target_message = ''
    #     if current_value == SwitchState.ON:
    #         msgdict = {
    #             'message': f'Loop is closed{target_message}! :star2:',
    #             'channel': '#observing'
    #         }
    #     elif current_value == SwitchState.OFF:
    #         msgdict = {
    #             'message': f'Loop is open!',
    #             'channel': '#observing'
    #         }
    #     print(msgdict)
    #     await vizzy_queue.put(msgdict)
    # await indi_notifier.add_notifier(
    #     'holoop.loop_state.toggle',
    #     handler=on_sky_loop_changes
    # )

async def register_transitions(indi_client, indi_notifier, vizzy_queue):
    print("Registering transition notifiers")
    async def function_out_transition(indi_id, previous_value, now):
        print('timeSeriesSimulator.function_out.value was=0, now=1')
    await indi_notifier.add_transition('timeSeriesSimulator.function_out.value', was=0, now=1, handler=function_out_transition)
    async def function_selected_transition(indi_id, current_value):
        if current_value is SwitchState.ON:
            msg = f'{indi_id} now {current_value}'
            await vizzy_queue.put(msg)
    for name in ['constant', 'cos', 'sin', 'square']:
        await indi_notifier.add_notifier(
            f'timeSeriesSimulator.function.{name}',
            handler=function_selected_transition
        )
    if MAGAOX_ROLE == 'AOC':
        await register_onsky(indi_client, indi_notifier, vizzy_queue)

async def spawn_tasks():
    loop = asyncio.get_event_loop()
    app.indi = make_indi_connection(potemkin=CONFIG['potemkin'])

    app.indi_batcher = INDIUpdateBatcher(app.indi)
    app.indi.add_async_watcher(app.indi_batcher.process_update)

    app.vizzy_queue = asyncio.Queue()

    app.indi_notifier = INDIStateTransitionNotifier(app.indi)
    await register_transitions(app.indi, app.indi_notifier, app.vizzy_queue)
    app.indi.add_async_watcher(app.indi_notifier.process_update)

    indi_coro = app.indi.run(reconnect_automatically=True)
    RUNNING_TASKS.add(loop.create_task(indi_coro))
    if CONFIG['potemkin']:
        fiddling_coro = app.indi.fiddle_connection_status()
        RUNNING_TASKS.add(loop.create_task(fiddling_coro))

    emit_updates_coro = emit_updates()
    RUNNING_TASKS.add(loop.create_task(emit_updates_coro))

    app.state.should_notify = os.environ.get('SUP_VIZZY') is not None
    if app.state.should_notify:
        print("Initialized vizzy relay")
    vizzy_relay_coro = vizzy_relay(app.vizzy_queue)
    RUNNING_TASKS.add(loop.create_task(vizzy_relay_coro))

async def cancel_tasks():
    await app.indi.stop()
    for task in RUNNING_TASKS:
        task.cancel()



app = Starlette(
    debug=True,
    routes=[
        Route('/', endpoint=index),
        Route('/indi', endpoint=indi),
        Route('/light-path', endpoint=light_path),
        Route('/demo', endpoint=demo),
        Route('/airmass', endpoint=airmass),
        # Mount('/video', routes=video.ROUTES),
        Route('/{path:path}', endpoint=catch_all),
    ],
    on_startup=[spawn_tasks],
    on_shutdown=[cancel_tasks],
    middleware=[
        Middleware(GZipMiddleware),
        Middleware(CORSMiddleware, allow_origins=['*'])
    ]
)


wrapped_app = socketio.ASGIApp(sio, app)

if __name__ == '__main__':
    console_entrypoint()
