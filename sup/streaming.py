"""Serving shmim image streams to browsers as viewcam feeds.

The wire protocol is viewcam's (viewarr-workspace/viewcam-proto/PROTOCOL.md):
each shmim is a feed, served as a WebSocket at ``/ws/viewcam/<shmim name>``,
carrying FRAME messages windowed by the client's ACKs. A camera view opens
a feed for the image and one each for its dark and saturation mask, if its
rtimv config names them, and combines them itself. The streams there are to watch, and each one's dark
and saturation mask, are listed as JSON at ``/ws/viewcam/`` (see
``stream_catalog``), found once at startup; any shmim can be watched by
name, listed or not. ``viewcam_proto`` is the protocol's Python reference,
copied verbatim from the submodule as the protocol intends servers to.

This is a Starlette app of its own so it can run in a process of its own,
behind the same reverse proxy as sup (``sup-stream``). The ImageStreamIO
binding is unguarded C, and a crash in it should not take INDI down with it;
frame traffic also shouldn't add jitter to INDI updates and audible alerts.
For development sup serves the same route itself (``serve_shmims``), so the
frontend connects to the same URL either way.

Each shmim is polled and encoded once, however many clients watch it, and
the same bytes go to all of them. What each client gets is up to its window:
while the window is full, only the newest frame waits for it.

Frames are compressed (``shuffle-zstd``) with ``viewcam_codec`` when it is
installed, and sent ``raw`` otherwise. Compressed frames are first rounded to
a fraction of their noise (PROTOCOL.md, "Quantization"), which ``noise``
estimates from each stream's own frames: noise is most of what a camera
frame holds, and precision finer than it is none a display can use. Frames
that don't measurably vary, like a dark, and single-byte images, like a
saturation mask, are sent exact.
"""
import asyncio
import dataclasses
import logging
import time

import uvicorn
import xconf
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute

from . import viewcam_proto
from .constants import INSTRUMENT_CONFIG_ROOT, SHMIM_STREAM_CONFIG_FILENAME
from .noise import NoiseTracker
from .shmim import SHMIM_NAME_PATTERN, ShmimPoller
from .stream_catalog import build_catalog
from .utils import OrjsonResponse

try:
    import viewcam_codec
except ImportError:
    viewcam_codec = None

log = logging.getLogger(__name__)

VIEWCAM_PATH = "/ws/viewcam/{name}"
# Beside the feeds, so the proxy rule that sends them to sup-stream sends this too.
CATALOG_PATH = "/ws/viewcam/"
# Close codes PROTOCOL.md asks for.
CLOSE_PROTOCOL_ERROR = 1002
CLOSE_UNSUPPORTED_DATA = 1003
# For refusing a name that can't be a shmim, before accepting.
CLOSE_POLICY_VIOLATION = 1008


@xconf.config
class ShmimStreamingConfig:
    max_fps : float = xconf.field(
        default=30.0,
        help="Most frames per second sent of any one stream, however fast it updates (0 for no limit)"
    )
    poll_interval_sec : float = xconf.field(
        default=0.005,
        help="How often to check a watched stream for a new frame"
    )
    reopen_interval_sec : float = xconf.field(
        default=1.0,
        help="How often to look for a watched stream that doesn't exist yet, or was recreated"
    )
    compress : bool = xconf.field(
        default=True,
        help="Compress frames with viewcam_codec, when it is installed"
    )
    noise_step : float = xconf.field(
        default=0.25,
        help="Round compressed frames to this fraction of their noise, estimated live from "
             "each stream's frames (0 to send them exact)"
    )
    slow_send_warning_sec : float = xconf.field(
        default=1.0,
        help="Log a warning when sending one frame to one client takes longer than this"
    )
    rtimv_config_dir : str = xconf.field(
        default=str(INSTRUMENT_CONFIG_ROOT),
        help="Directory of rtimv_*.conf files, which define the streams listed first, "
             "and their darks and saturation masks, which aren't listed (empty to skip)"
    )
    shmim_dir : str = xconf.field(
        default="",
        help="Directory whose other shmims are listed after (empty for ImageStreamIO's: "
             "$MILK_SHM_DIR, else /milk/shm, else /tmp)"
    )


@dataclasses.dataclass(frozen=True)
class EncodedFrame:
    seq : int
    message : bytes


def plane_of(frame):
    """A frame as the binding returns it, indexed [x, y] (or [x, y, z]) in
    column-major order, as the protocol's image.

    Column-major [x, y] is the protocol's row-major layout with x fastest, so
    ``frame.T`` is the plane to send as it stands, no copy needed; row 0 is
    y = 0, the bottom row, as for the protocol. The protocol is 2D, so a
    one-axis stream is sent as a single row, and a cube as its slices
    stacked along y.
    """
    return frame.T


def encode_frame(seq, frame, compress, noise=None, noise_step=0.25):
    """A FRAME message for a frame as the binding returns it (see
    ``plane_of``). Compressed, and with a ``noise`` model, its values are
    rounded to ``noise_step`` of their noise and sent as codes."""
    width = frame.shape[0]
    height = frame.size // width if width else 0
    dtype = viewcam_proto.dtype_code(frame.dtype)
    plane = plane_of(frame)
    if not (compress and viewcam_codec is not None and frame.size):
        return viewcam_proto.encode_frame(seq, width, height, dtype, plane, viewcam_proto.CODEC_RAW)
    quantization = None
    if noise is not None:
        try:
            codes, code_offset = viewcam_codec.quantize(
                plane, noise.bias, noise.read_noise, noise.noise_slope, noise_step)
        except ValueError:
            # Values the model can't round, like NaN: this frame goes exact.
            pass
        else:
            plane, dtype = codes, viewcam_proto.dtype_code(codes.dtype)
            quantization = viewcam_proto.Quantization(
                code_offset, noise.bias, noise.read_noise, noise.noise_slope, noise_step)
    payload = viewcam_codec.encode(plane, zstd=True)
    return viewcam_proto.encode_frame(
        seq, width, height, dtype, payload, viewcam_proto.CODEC_SHUFFLE_ZSTD, quantization)


class SharedStream:
    """One shmim, polled and encoded once for every client watching it."""
    def __init__(self, name, config):
        self.name = name
        self.feeds = set()
        self._compress = config.compress and viewcam_codec is not None
        self._noise_step = config.noise_step
        self._noise = NoiseTracker() if self._compress and config.noise_step > 0 else None
        self._retry_sec = config.reopen_interval_sec
        self._last_seq = 0
        self._seq_offset = 0
        self._poller = ShmimPoller(
            name,
            poll_interval=config.poll_interval_sec,
            min_frame_interval=1 / config.max_fps if config.max_fps > 0 else 0.0,
            reopen_interval=config.reopen_interval_sec,
        )
        # A feed with no image is told so with an empty frame. One whose shmim
        # exists waits for its first frame instead, which the poller yields
        # straight away, rather than flash "no image" first.
        self.latest = None
        if not self._poller.exists():
            self.latest = EncodedFrame(0, viewcam_proto.encode_empty_frame(0, 1))
        self._task = asyncio.create_task(self._run())

    def _seq_for(self, cnt0):
        """The camera's counter as seq, kept increasing when it restarts with
        a recreated shmim, as the protocol requires."""
        seq = cnt0 + self._seq_offset
        if seq <= self._last_seq:
            self._seq_offset = self._last_seq + 1 - cnt0
            seq = self._last_seq + 1
        self._last_seq = seq
        return seq

    def _noise_model(self, frame):
        """The noise to round this frame to, or None to send it exact."""
        if self._noise is None or frame.itemsize == 1:
            return None
        model = self._noise.update(plane_of(frame))
        if model is not None and frame.dtype.kind in "iu":
            # Integers are already rounded to 1: no finer steps than that.
            model = dataclasses.replace(model, read_noise=max(model.read_noise, 1 / self._noise_step))
        return model

    def _encode_now(self, seq, frame):
        return encode_frame(seq, frame, self._compress, self._noise_model(frame), self._noise_step)

    async def _encode(self, seq, frame):
        if self._compress:
            # The codec releases the GIL, so a large frame needn't stall the loop.
            return await asyncio.to_thread(self._encode_now, seq, frame)
        return self._encode_now(seq, frame)

    async def _run(self):
        while True:
            try:
                async for cnt0, frame in self._poller.frames():
                    seq = self._seq_for(cnt0)
                    self.latest = EncodedFrame(seq, await self._encode(seq, frame))
                    for feed in list(self.feeds):
                        feed.offer(self.latest)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception(f"Following shmim {self.name} failed; starting over")
                await asyncio.sleep(self._retry_sec)

    def stop(self):
        self._task.cancel()


class ViewcamFeed:
    """One client's connection to one stream. Sends the newest frame
    whenever the client's window has room, and nothing else: a slow or
    stalled client falls behind by at most its window, and delays only
    itself."""
    def __init__(self, websocket, stream, config):
        self.websocket = websocket
        self.stream = stream
        self.window = viewcam_proto.SendWindow()
        self.pending = None
        self._slow_send_warning_sec = config.slow_send_warning_sec
        self._wake = asyncio.Event()
        self._sender = None

    @property
    def where(self):
        peer = getattr(self.websocket, 'client', None)
        return f"{peer.host}:{peer.port}" if peer is not None else "unknown client"

    def offer(self, frame):
        self.pending = frame
        self._wake.set()

    def on_ack(self, message):
        self.window.on_ack(viewcam_proto.decode_ack(message))
        self._wake.set()

    def start(self):
        self._sender = asyncio.create_task(self._send_loop())

    def stop(self):
        if self._sender is not None:
            self._sender.cancel()
            self._sender = None

    async def _send_loop(self):
        try:
            while True:
                frame = self.pending
                if frame is not None and self.window.may_send(len(frame.message)):
                    self.pending = None
                    self.window.sent(len(frame.message))
                    started_at = time.monotonic()
                    await self.websocket.send_bytes(frame.message)
                    elapsed = time.monotonic() - started_at
                    if elapsed > self._slow_send_warning_sec:
                        log.warning(
                            f"Slow viewcam send: {elapsed:.2f}s to {self.where} "
                            f"for {len(frame.message)} bytes of {self.stream.name}"
                        )
                    continue
                await self._wake.wait()
                # Cleared only after waking, then rechecked, so an offer or
                # ack landing in between is never lost.
                self._wake.clear()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.debug(f"Swallowed exception sending to {self.where}: {type(e)} {e}")


class ShmimHub:
    """The streams being watched, each started by its first feed and stopped
    with its last. Nothing runs at startup but finding the streams to list,
    so the hub works the same as its own app or mounted in sup, where a
    sub-app's lifespan never runs."""
    def __init__(self, config):
        self.config = config
        self.streams = {}
        self.catalog = build_catalog(config.rtimv_config_dir or None, config.shmim_dir or None)

    def subscribe(self, name, websocket):
        stream = self.streams.get(name)
        if stream is None:
            stream = self.streams[name] = SharedStream(name, self.config)
            log.debug(f"Started following shmim {name}")
        feed = ViewcamFeed(websocket, stream, self.config)
        stream.feeds.add(feed)
        if stream.latest is not None:
            feed.offer(stream.latest)
        return feed

    def unsubscribe(self, feed):
        stream = feed.stream
        stream.feeds.discard(feed)
        if not stream.feeds and self.streams.get(stream.name) is stream:
            stream.stop()
            del self.streams[stream.name]
            log.debug(f"Stopped following shmim {stream.name}")

    async def endpoint(self, websocket):
        name = websocket.path_params["name"]
        if not SHMIM_NAME_PATTERN.fullmatch(name):
            await websocket.close(code=CLOSE_POLICY_VIOLATION)
            return
        await websocket.accept()
        feed = self.subscribe(name, websocket)
        feed.start()
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break
                data = message.get("bytes")
                if data is None:
                    log.debug(f"Text message from {feed.where} on viewcam feed {name}")
                    await websocket.close(code=CLOSE_UNSUPPORTED_DATA)
                    break
                try:
                    feed.on_ack(data)
                except viewcam_proto.ProtocolError as e:
                    log.debug(f"Bad message from {feed.where} on viewcam feed {name}: {e}")
                    await websocket.close(code=CLOSE_PROTOCOL_ERROR)
                    break
        finally:
            feed.stop()
            self.unsubscribe(feed)

    async def list_streams(self, request):
        return OrjsonResponse(self.catalog.to_json())

    def routes(self):
        return [
            Route(CATALOG_PATH, endpoint=self.list_streams),
            WebSocketRoute(VIEWCAM_PATH, endpoint=self.endpoint),
        ]


def create_app(config, debug=False):
    return Starlette(debug=debug, routes=ShmimHub(config).routes())


@xconf.config
class ShmimStreamServer(xconf.Command):
    """Serve shmim image streams to browsers, in a process apart from sup"""
    @classmethod
    def get_default_config_path(cls):
        return INSTRUMENT_CONFIG_ROOT / SHMIM_STREAM_CONFIG_FILENAME

    bind_host : str = xconf.field(default="127.0.0.1", help="Listening address (0.0.0.0 for all)")
    bind_port : int = xconf.field(default=9192, help="Listening TCP port")
    debug_mode : bool = xconf.field(default=True, help="Initialize Starlette framework in debug mode")
    streaming : ShmimStreamingConfig = xconf.field(default_factory=ShmimStreamingConfig)

    def main(self):
        if self.streaming.compress and viewcam_codec is None:
            log.warning("viewcam_codec is not installed; frames will be sent uncompressed")
        uvicorn.run(
            create_app(self.streaming, self.debug_mode),
            host=self.bind_host,
            port=self.bind_port,
            # PROTOCOL.md: LZ4 payloads don't deflate, and the CPU it costs is latency.
            ws_per_message_deflate=False,
        )
