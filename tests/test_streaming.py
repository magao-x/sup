"""Tests for serving shmims as viewcam feeds, against sup.isio_mock.

The delivery rules pinned down here are the ones that let one stream reach
many browsers on very different links: each stream is followed once however
many clients watch it, a client is sent nothing beyond its window, and when
the window frees up what it gets next is the newest frame, not the oldest.
Frames are decoded here independently of the server, so the layout the
protocol promises (row-major, x fastest, row 0 at y = 0) is checked too.
"""
import contextlib
import dataclasses
import pathlib
import struct
import time

import numpy as np
import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from sup import isio_mock, shmim, streaming, viewcam_proto
from sup.streaming import ShmimHub, ShmimStreamingConfig

viewcam_codec = pytest.importorskip("viewcam_codec")

VENDORED_FROM = pathlib.Path(__file__).parent.parent / "viewarr-workspace/viewcam-proto/python/viewcam_proto.py"
FRAME_HEADER = struct.Struct("<4sBBHQIIBBBBIqdddd")


@pytest.fixture(autouse=True)
def mock_isio(tmp_path, monkeypatch):
    monkeypatch.setenv("MILK_SHM_DIR", str(tmp_path))
    monkeypatch.setattr(shmim, "ISIO", isio_mock)


def fast_config(**overrides):
    settings = dict(max_fps=0, poll_interval_sec=0.001, reopen_interval_sec=0.02, rtimv_config_dir="")
    settings.update(overrides)
    return ShmimStreamingConfig(**settings)


@contextlib.contextmanager
def serve(config):
    hub = ShmimHub(config)
    with TestClient(Starlette(routes=hub.routes())) as client:
        yield hub, client


@pytest.fixture
def hub_and_client():
    with serve(fast_config()) as served:
        yield served


@pytest.fixture
def hub(hub_and_client):
    return hub_and_client[0]


@pytest.fixture
def client(hub_and_client):
    return hub_and_client[1]


def make_image(name, data):
    img = isio_mock.Image()
    assert img.create(name, data) == 0
    return img


def frame(value, shape=(4, 3), dtype=np.uint16):
    return np.full(shape, value, dtype=dtype)


@dataclasses.dataclass
class Received:
    seq: int
    width: int
    height: int
    codec: int
    pixels: np.ndarray | None
    # For a quantized frame, its noise model and step; None for an exact one.
    quantization: viewcam_proto.Quantization | None = None


def decode(message):
    """A frame, decoded independently of the server's encoder."""
    (magic, version, kind, _, seq, width, height, dtype, codec, quantized, _, encoded_len,
     *params) = FRAME_HEADER.unpack_from(message)
    assert (magic, version, kind) == (b"VCAM", 1, viewcam_proto.KIND_FRAME)
    payload = message[FRAME_HEADER.size:]
    assert len(payload) == encoded_len
    dtype = np.dtype(viewcam_proto.DTYPES[dtype][0])
    if width * height == 0:
        pixels = None
    elif codec == viewcam_proto.CODEC_RAW:
        pixels = np.frombuffer(payload, dtype).reshape(height, width)
    else:
        shuffle = codec != viewcam_proto.CODEC_LZ4
        zstd = codec == viewcam_proto.CODEC_SHUFFLE_ZSTD
        pixels = viewcam_codec.decode(payload, dtype, (height, width), shuffle=shuffle, zstd=zstd)
    quantization = None
    if quantized:
        quantization = viewcam_proto.Quantization(*params)
        q = quantization
        pixels = viewcam_codec.dequantize(pixels, q.code_offset, q.bias, q.read_noise, q.noise_slope, q.step)
    else:
        assert not any(params)
    return Received(seq, width, height, codec, pixels, quantization)


class Viewer:
    """The client side of one feed: acknowledges what it receives, and asks
    for the window it was given."""
    def __init__(self, ws, window_frames=1, window_bytes=0):
        self.ws = ws
        self.frames = self.bytes = 0
        self.window = (window_frames, window_bytes)
        self.ack()

    def ack(self):
        ack = viewcam_proto.Ack(self.frames, self.bytes, *self.window)
        self.ws.send_bytes(viewcam_proto.encode_ack(ack))

    def receive(self, ack=True):
        message = self.ws.receive_bytes()
        self.frames += 1
        self.bytes += len(message)
        if ack:
            self.ack()
        return decode(message)

    def set_window(self, window_frames, window_bytes=0):
        self.window = (window_frames, window_bytes)
        self.ack()


@contextlib.contextmanager
def watch(client, name, **window):
    with client.websocket_connect(f"/ws/viewcam/{name}") as ws:
        yield Viewer(ws, **window)


def wait_for(condition, timeout=5):
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.005)


def newest_seq(hub, name):
    latest = hub.streams[name].latest
    return latest.seq if latest is not None else None


@pytest.mark.parametrize("compress, codec", [
    (False, viewcam_proto.CODEC_RAW),
    (True, viewcam_proto.CODEC_SHUFFLE_ZSTD),
])
def test_frames_arrive_row_major_with_x_fastest(compress, codec):
    pixels = np.arange(12, dtype=np.uint16).reshape(4, 3)  # [x, y]
    make_image("cam", pixels)
    with serve(fast_config(compress=compress)) as (_, client), watch(client, "cam") as viewer:
        got = viewer.receive()
    assert (got.width, got.height, got.codec) == (4, 3, codec)
    assert got.seq == 1
    # Row y of the protocol's image is column y of the binding's [x, y] array.
    np.testing.assert_array_equal(got.pixels, pixels.T)


def noisy(seed, shape=(64, 48), level=1000.0, read_noise=10.0, photons=True, dtype=np.uint16):
    """A frame of read noise and (unless not ``photons``) photon noise,
    amplified, around ``level``."""
    rng = np.random.default_rng(seed)
    sigma = np.sqrt(read_noise ** 2 + (4.0 * level if photons else 0))
    return np.rint(level + rng.normal(0, sigma, shape)).astype(dtype)


def test_noisy_frames_are_rounded_to_a_quarter_of_their_noise(client):
    original = noisy(1)
    make_image("cam", original)
    with watch(client, "cam") as viewer:
        got = viewer.receive()
    q = got.quantization
    assert q is not None and q.step == 0.25
    assert got.pixels.dtype == np.float32
    # Each value is back within half a step of the noise the model gives it.
    values = original.T.astype(np.float64)
    noise = np.sqrt(q.read_noise ** 2 + q.noise_slope * np.maximum(values - q.bias, 0))
    assert np.all(np.abs(got.pixels - values) <= 0.5 * q.step * noise * 1.05)
    # The model is about right: sqrt(10^2 + 4 x 1000) is about 64.
    assert 40 < np.median(noise) < 90


@pytest.mark.parametrize("pixels", [
    np.eye(4, dtype=np.uint8),                          # a saturation mask: single bytes
    np.full((8, 6), 512, dtype=np.uint16),              # nothing varies
    np.tile(np.arange(6, dtype=np.uint16), (8, 1)).T,   # noiseless bands
])
def test_frames_without_measurable_noise_are_sent_exact(client, pixels):
    make_image("dark", pixels)
    with watch(client, "dark") as viewer:
        got = viewer.receive()
    assert got.quantization is None
    np.testing.assert_array_equal(got.pixels, pixels.T)


@pytest.mark.parametrize("settings", [dict(noise_step=0), dict(compress=False)])
def test_frames_can_be_sent_exact(settings):
    original = noisy(2)
    make_image("cam", original)
    with serve(fast_config(**settings)) as (_, client), watch(client, "cam") as viewer:
        got = viewer.receive()
    assert got.quantization is None
    np.testing.assert_array_equal(got.pixels, original.T)


def test_integer_frames_are_not_rounded_finer_than_one(client):
    # Read noise of 2 counts: a quarter of it would be a step of 1/2.
    original = noisy(3, level=100.0, read_noise=2.0, photons=False)
    make_image("cam", original)
    with watch(client, "cam") as viewer:
        got = viewer.receive()
    q = got.quantization
    assert q is not None and q.read_noise * q.step >= 1


def test_a_cube_is_sent_as_slices_stacked_along_y(client):
    pixels = np.arange(24, dtype=np.float32).reshape(4, 3, 2)
    make_image("cube", pixels)
    with watch(client, "cube") as viewer:
        got = viewer.receive()
    assert (got.width, got.height) == (4, 6)
    np.testing.assert_array_equal(got.pixels, np.vstack([pixels[:, :, 0].T, pixels[:, :, 1].T]))


def test_a_vector_is_sent_as_one_row(client):
    make_image("modes", np.arange(5, dtype=np.float64))
    with watch(client, "modes") as viewer:
        got = viewer.receive()
    assert (got.width, got.height) == (5, 1)


def test_each_ack_lets_the_next_frame_through(client):
    img = make_image("cam", frame(0))
    with watch(client, "cam") as viewer:
        for value in range(1, 6):
            assert viewer.receive().pixels[0, 0] == value - 1
            img.write(frame(value))
        got = viewer.receive()
    assert (got.seq, got.pixels[0, 0]) == (6, 5)


def test_a_full_window_waits_then_gets_the_newest_frame(client, hub):
    img = make_image("cam", frame(0))
    with watch(client, "cam", window_frames=2) as viewer:
        first = viewer.receive(ack=False)
        img.write(frame(1))
        second = viewer.receive(ack=False)
        assert (first.seq, second.seq) == (1, 2)
        # Two frames unacknowledged fill the window; these must wait.
        for value in range(2, 6):
            img.write(frame(value))
        wait_for(lambda: newest_seq(hub, "cam") == 6)
        viewer.ack()
        got = viewer.receive()
    assert (got.seq, got.pixels[0, 0]) == (6, 5)


def test_a_paused_feed_resumes_with_the_newest_frame(client, hub):
    img = make_image("cam", frame(0))
    with watch(client, "cam") as viewer:
        viewer.receive()
        viewer.set_window(0)
        for value in range(1, 4):
            img.write(frame(value))
        wait_for(lambda: newest_seq(hub, "cam") == 4)
        viewer.set_window(1)
        got = viewer.receive()
    assert (got.seq, got.pixels[0, 0]) == (4, 3)


def test_a_missing_shmim_is_an_empty_frame_until_it_appears(client):
    with watch(client, "late") as viewer:
        empty = viewer.receive()
        assert (empty.width, empty.height, empty.pixels) == (0, 0, None)
        make_image("late", frame(3))
        got = viewer.receive()
    assert got.seq > empty.seq
    assert got.pixels[0, 0] == 3


def test_seq_keeps_increasing_when_the_shmim_is_recreated(client):
    img = make_image("cam", frame(0))
    with watch(client, "cam") as viewer:
        for value in range(1, 4):
            viewer.receive()
            img.write(frame(value))
        before = viewer.receive()
        assert before.seq == 4
        # A restarted camera counts from 1 again.
        make_image("cam", frame(9, shape=(8, 8)))
        after = viewer.receive()
    assert after.seq > before.seq
    assert (after.width, after.pixels[0, 0]) == (8, 9)


def test_one_stream_is_followed_once_for_every_client(client, hub):
    make_image("cam_dark", frame(7))
    with watch(client, "cam_dark") as first:
        first.receive()
        with watch(client, "cam_dark") as second:
            # Nothing new is written, as with a dark written once: the second
            # client still gets the current frame straight away.
            assert second.receive().pixels[0, 0] == 7
            assert len(hub.streams) == 1
            assert len(hub.streams["cam_dark"].feeds) == 2
        wait_for(lambda: len(hub.streams["cam_dark"].feeds) == 1)
    wait_for(lambda: not hub.streams)


@pytest.mark.parametrize("send, code", [
    (lambda ws: ws.send_text("hello"), streaming.CLOSE_UNSUPPORTED_DATA),
    (lambda ws: ws.send_bytes(b"not a viewcam message at all...."), streaming.CLOSE_PROTOCOL_ERROR),
    # Acknowledging a frame that was never sent.
    (lambda ws: ws.send_bytes(viewcam_proto.encode_ack(viewcam_proto.Ack(5, 500, 1, 0))),
     streaming.CLOSE_PROTOCOL_ERROR),
])
def test_protocol_errors_close_the_feed(client, send, code):
    with client.websocket_connect("/ws/viewcam/cam") as ws:
        send(ws)
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_bytes()
    assert closed.value.code == code


@pytest.mark.parametrize("name", [".hidden", "bad name", "-x"])
def test_names_that_cannot_be_shmims_are_refused(client, name):
    with pytest.raises(WebSocketDisconnect) as refused:
        with client.websocket_connect(f"/ws/viewcam/{name}"):
            pass
    assert refused.value.code == streaming.CLOSE_POLICY_VIOLATION


@pytest.mark.skipif(not VENDORED_FROM.exists(), reason="viewarr-workspace submodule not checked out")
def test_vendored_protocol_matches_the_submodule():
    vendored = pathlib.Path(viewcam_proto.__file__).read_bytes()
    assert vendored == VENDORED_FROM.read_bytes(), (
        f"sup/viewcam_proto.py differs from {VENDORED_FROM}; copy it over again")
