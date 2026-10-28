#!/usr/bin/env python
"""A stand-in for the audibleAlerts xApp, for developing and testing sup's
browser-side alert playback without a MagAO-X instrument.

It speaks just enough INDI to be the ``maggieo_x`` device: it accepts client
connections, defines the ``playback`` text vector, and emits an update for it
on demand. Alongside the INDI port it runs a small HTTP control surface, so a
test (or a developer poking at it with a browser) can trigger an utterance:

    POST /emit?file=<clip>&speech=<text>   make the device "play" a clip
    POST /log?text=<text>                  send an INDI log message, e.g. "ERR  oops"
    GET  /clips                            list the clips in the cache
    GET  /health                           readiness check

Clips are generated on startup, so the cache directory this writes is the one
to point ``sup``'s ``audible_alerts_cache_root`` at::

    python tests/fake_audible_alerts_device.py --cache-root /tmp/sup-alerts &
    uv run sup indi.port=17624 audible_alerts_cache_root=/tmp/sup-alerts

This is deliberately not a general INDI simulator: it publishes one property,
because that is the whole interface the browser player depends on, plus log
messages on demand, for the log viewer's tests.
"""
import argparse
import asyncio
import datetime
import http.server
import json
import math
import pathlib
import struct
import threading
import urllib.parse
import wave
from xml.sax.saxutils import escape, quoteattr

DEVICE = "maggieo_x"
PROPERTY = "playback"

# Named the way the real device names things: synthesized speech is called
# after a hash of its text and voice, recordings keep their own filenames, and
# anything whose text was substituted at playback time goes under temp/.
SAMPLE_CLIPS = {
    "a1b2c3d4e5.wav": 440.0,
    "walkup_example.wav": 523.25,
    "temp/f6e5d4c3b2.wav": 330.0,
}


def iso_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def write_tone(path: pathlib.Path, freq_hz: float, duration_sec: float = 0.4, rate: int = 22050):
    """Write a short tone, so each clip is audibly distinct when playing by ear."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(duration_sec * rate)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b''.join(
            struct.pack(
                '<h',
                int(32767 * 0.3 * math.sin(2 * math.pi * freq_hz * i / rate)
                    * min(1.0, i / 400, (frames - i) / 800))
            )
            for i in range(frames)
        ))


def populate_cache(cache_root: pathlib.Path) -> list[str]:
    cache_root.mkdir(parents=True, exist_ok=True)
    for relative_path, freq_hz in SAMPLE_CLIPS.items():
        write_tone(cache_root / relative_path, freq_hz)
    return sorted(SAMPLE_CLIPS)


def def_property_xml() -> bytes:
    return (
        f'<defTextVector device="{DEVICE}" name="{PROPERTY}" state="Ok" perm="ro" '
        f'timestamp="{iso_now()}">'
        '<defText name="speech"></defText>'
        '<defText name="voice"></defText>'
        '<defText name="file"></defText>'
        '</defTextVector>\n'
    ).encode()


def set_property_xml(file: str, speech: str, voice: str, timestamp: str) -> bytes:
    return (
        f'<setTextVector device="{DEVICE}" name="{PROPERTY}" state="Ok" '
        f'timestamp={quoteattr(timestamp)}>'
        f'<oneText name="speech">{escape(speech)}</oneText>'
        f'<oneText name="voice">{escape(voice)}</oneText>'
        f'<oneText name="file">{escape(file)}</oneText>'
        '</setTextVector>\n'
    ).encode()


def log_message_xml(text: str, timestamp: str) -> bytes:
    return (
        f'<message device="{DEVICE}" timestamp={quoteattr(timestamp)} message={quoteattr(text)}/>\n'
    ).encode()


class FakeDevice:
    def __init__(self, cache_root: pathlib.Path):
        self.cache_root = cache_root
        self.clips = populate_cache(cache_root)
        self.clients: list[asyncio.StreamWriter] = []
        self.loop: asyncio.AbstractEventLoop | None = None
        self.emitted: list[dict] = []

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.clients.append(writer)
        writer.write(def_property_xml())
        await writer.drain()
        try:
            # The client's getProperties (and anything else it says) needs
            # draining, but nothing it can say changes what this device does.
            while await reader.read(4096):
                pass
        except ConnectionError:
            pass
        finally:
            if writer in self.clients:
                self.clients.remove(writer)
            writer.close()

    async def send_to_clients(self, payload: bytes) -> int:
        delivered = 0
        for writer in list(self.clients):
            try:
                writer.write(payload)
                await writer.drain()
                delivered += 1
            except ConnectionError:
                if writer in self.clients:
                    self.clients.remove(writer)
        return delivered

    async def emit(self, file: str, speech: str, voice: str) -> dict:
        timestamp = iso_now()
        delivered = await self.send_to_clients(set_property_xml(file, speech, voice, timestamp))
        record = {'file': file, 'speech': speech, 'voice': voice,
                  'timestamp': timestamp, 'clients': delivered}
        self.emitted.append(record)
        return record

    def emit_threadsafe(self, file: str, speech: str, voice: str) -> dict:
        future = asyncio.run_coroutine_threadsafe(self.emit(file, speech, voice), self.loop)
        return future.result(timeout=5)

    def log_threadsafe(self, text: str) -> dict:
        payload = log_message_xml(text, iso_now())
        future = asyncio.run_coroutine_threadsafe(self.send_to_clients(payload), self.loop)
        return {'text': text, 'clients': future.result(timeout=5)}


def make_control_handler(device: FakeDevice):
    class ControlHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def _respond(self, status: int, body: dict):
            encoded = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(encoded)))
            # The browser test drives this from page context in some setups.
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):
            route = urllib.parse.urlparse(self.path).path
            if route == '/health':
                self._respond(200, {'ok': True, 'clients': len(device.clients)})
            elif route == '/clips':
                self._respond(200, {'clips': device.clips, 'cache_root': str(device.cache_root)})
            elif route == '/emitted':
                self._respond(200, {'emitted': device.emitted})
            else:
                self._respond(404, {'error': 'no such control route'})

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            if parsed.path == '/log':
                self._respond(200, device.log_threadsafe(query.get('text', ['INFO hello'])[0]))
                return
            if parsed.path != '/emit':
                self._respond(404, {'error': 'no such control route'})
                return
            file = query.get('file', [device.clips[0]])[0]
            speech = query.get('speech', [f'playing {file}'])[0]
            voice = query.get('voice', ['en_GB-cori-high'])[0]
            self._respond(200, device.emit_threadsafe(file, speech, voice))

        def log_message(self, *args):
            pass  # the test runner has its own output

    return ControlHandler


async def main_async(args):
    device = FakeDevice(pathlib.Path(args.cache_root))
    device.loop = asyncio.get_running_loop()

    control = http.server.ThreadingHTTPServer(
        ('127.0.0.1', args.control_port), make_control_handler(device)
    )
    threading.Thread(target=control.serve_forever, daemon=True).start()

    server = await asyncio.start_server(device.handle_client, '127.0.0.1', args.indi_port)
    print(f"fake {DEVICE}: INDI on {args.indi_port}, control on {args.control_port}, "
          f"clips in {device.cache_root}", flush=True)
    async with server:
        await server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--indi-port', type=int, default=17624)
    parser.add_argument('--control-port', type=int, default=17625)
    parser.add_argument('--cache-root', default='/tmp/sup-fake-audible-alerts')
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
