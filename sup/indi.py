import asyncio
from pprint import pformat
from purepyindi import client
from purepyindi.eventful import AsyncINDIClient, RECONNECTION_DELAY
from purepyindi.constants import (
    INDIPropertyKind, INDIActions, DEFAULT_HOST, DEFAULT_PORT, parse_string_into_enum, SwitchState,
    PropertyState, ConnectionStatus
)
from purepyindi.generator import format_datetime_as_iso
from purepyindi.parser import parse_iso_to_datetime
import purepyindi.log as log


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

class SupINDIClient(AsyncINDIClient):
    def __init__(self, sio, *args, **kwargs):
        self.sio = sio
        self._status = ConnectionStatus.STARTING
        super().__init__(*args, **kwargs)
    async def run(self, reconnect_automatically=False):
        while self.status is not ConnectionStatus.STOPPED:
            try:
                reader_handle, writer_handle = await asyncio.open_connection(
                    self.host,
                    self.port
                )
                addr = writer_handle.get_extra_info("peername")
                log.info(f"Connected to {addr!r}")
                self.status = ConnectionStatus.CONNECTED
                await self.sio.emit('indi_connection_status', {'status': self.status.name})
                self._reader = asyncio.ensure_future(self._handle_inbound(reader_handle))
                self._writer = asyncio.ensure_future(self._handle_outbound(writer_handle))
                self.get_properties()

                # Reload state after we take a second to process properties
                await asyncio.sleep(1)
                # Emitting state reload message
                await self.sio.emit('indi_init', self.to_jsonable())

                try:
                    await asyncio.gather(
                        self._reader, self._writer
                    )
                except asyncio.CancelledError:
                    continue
            except ConnectionError as e:
                log.warn(f"Failed to connect: {repr(e)}")

                if reconnect_automatically:
                    log.warn(f"Retrying in {RECONNECTION_DELAY} seconds")
            except Exception as e:
                log.warn(f"Swallowed exception: {type(e)}, {e}")
                raise
            finally:
                self._cancel_tasks()
            if reconnect_automatically:
                await self.sio.emit('indi_connection_status', {'connected': False})
                self.status = ConnectionStatus.RECONNECTING
                await asyncio.sleep(RECONNECTION_DELAY)
            else:
                await self.sio.emit('indi_connection_status', {'connected': False})
                raise ConnectionError(f"Got disconnected from {self.host}:{self.port}, not attempting reconnection")

class BogusINDIClient(SupINDIClient):
    KIND_TO_CLASSES = {
        'num': (client.NumberProperty, client.NumberElement),
        'txt': (client.TextProperty, client.TextElement),
        'swt': (client.SwitchProperty, client.SwitchElement),
        'lgt': (client.LightProperty, client.LightElement),
    }
    def __init__(self, sio, initial_state):
        super().__init__(sio, host=None, port=None)
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
        for watcher in self.async_watchers:
            asyncio.create_task(watcher(update, did_anything_change=True))
        print("Applied faux-indi-new update", pformat(update))
        async def clear_busy():
            update['action'] = INDIActions.PROPERTY_SET
            update['property']['state'] = original_state
            await asyncio.sleep(2)
            self.apply_update(update)
            for watcher in self.async_watchers:
                await watcher(update, did_anything_change=True)
        asyncio.create_task(clear_busy())
    async def fiddle_connection_status(self):
        while True:
            print("Toggling connection status")
            self.status = ConnectionStatus.RECONNECTING
            await asyncio.sleep(4)
            self.status = ConnectionStatus.CONNECTED
            await asyncio.sleep(4)
    async def run(self, *args, **kwargs):
        self.status = ConnectionStatus.CONNECTED
        return

