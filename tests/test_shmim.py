"""Tests for following shmims from the event loop, against sup.isio_mock."""
import asyncio
import time
import warnings

import numpy as np
import pytest

from sup import isio_mock, shmim
from sup.shmim import ShmimPoller

import fake_camera


@pytest.fixture(autouse=True)
def mock_isio(tmp_path, monkeypatch):
    monkeypatch.setenv("MILK_SHM_DIR", str(tmp_path))
    monkeypatch.setattr(shmim, "ISIO", isio_mock)


def make_image(name, data):
    img = isio_mock.Image()
    assert img.create(name, data) == 0
    return img


def frame(value, shape=(4, 3)):
    return np.full(shape, value, dtype=np.float32)


def follow(poller, collect, act):
    """Run act(frames_so_far) between frames until collect frames arrive, all
    inside one event loop, failing rather than hanging if they never do."""
    async def run():
        seen = []
        stream = poller.frames()
        async def gather():
            async for cnt0, _, data in stream:
                seen.append((cnt0, data))
                if len(seen) == collect:
                    return
                act(seen)
        try:
            await asyncio.wait_for(gather(), timeout=5)
        finally:
            await stream.aclose()
        return seen
    with warnings.catch_warnings():
        warnings.simplefilter("error", isio_mock.BlockingWaitWarning)
        return asyncio.run(run())


def fast_poller(name, **kwargs):
    return ShmimPoller(name, poll_interval=0.001, reopen_interval=0.02, **kwargs)


def test_yields_each_new_frame_once():
    writer = make_image("cam", frame(0))
    seen = follow(fast_poller("cam"), 3, lambda seen: writer.write(frame(len(seen))))
    assert [cnt0 for cnt0, _ in seen] == [1, 2, 3]
    assert [data[0, 0] for _, data in seen] == [0, 1, 2]


def test_waits_for_the_stream_to_appear():
    created = []  # keeps the writer's Image alive

    async def run():
        async def create_later():
            await asyncio.sleep(0.05)
            created.append(make_image("late", frame(9)))
        creator = asyncio.create_task(create_later())
        stream = fast_poller("late").frames()
        try:
            return await asyncio.wait_for(anext(stream), timeout=5)
        finally:
            await stream.aclose()
            await creator

    cnt0, _, data = asyncio.run(run())
    assert data[0, 0] == 9


def test_decimates_to_min_frame_interval():
    writer = make_image("fast", frame(0))

    async def run():
        async def write_fast():
            for i in range(1, 40):
                await asyncio.sleep(0.005)
                writer.write(frame(i))
        writer_task = asyncio.create_task(write_fast())
        seen = []
        stream = fast_poller("fast", min_frame_interval=0.05).frames()
        try:
            async for cnt0, _, _ in stream:
                seen.append(cnt0)
                if writer_task.done():
                    break
        finally:
            await stream.aclose()
        return seen

    seen = asyncio.run(run())
    # Roughly 0.2 s of writes at one frame per 50 ms; far fewer than the 40 written.
    assert 2 <= len(seen) <= 8
    assert seen == sorted(seen)


def test_reopens_a_recreated_stream():
    make_image("roi", frame(1))
    seen = follow(fast_poller("roi"), 2,
                  lambda seen: make_image("roi", frame(2, shape=(8, 8))))
    assert seen[0][1].shape == (4, 3)
    assert seen[1][1].shape == (8, 8)
    assert seen[1][1][0, 0] == 2


def test_rejects_a_frame_caught_mid_write():
    img = make_image("torn", frame(0))
    img._hdr["write"] = 1
    assert ShmimPoller._read(img) is None
    img._hdr["write"] = 0
    cnt0, _, data = ShmimPoller._read(img)
    assert cnt0 == 1


def test_reads_when_a_frame_was_acquired():
    img = make_image("stamped", frame(0))
    # Unset until an update stamps it: write() alone doesn't, in the binding
    # or the mock, which is why sup's fake camera frames have none.
    img.write(frame(1))
    assert ShmimPoller._read(img)[1] == 0
    # update() does, as ImageStreamIO_UpdateIm does for the cameras.
    img.update()
    _, acq_time_ns, _ = ShmimPoller._read(img)
    assert abs(acq_time_ns / 1e9 - time.time()) < 60


def test_fake_camera_streams_agree():
    rng = np.random.default_rng(1)
    width, height = 96, 64
    dark = fake_camera.dark_frame(width, height, rng)
    mask = fake_camera.numeral_mask("7", width, height)
    camera = fake_camera.camera_frame(mask, dark, rng)
    assert dark.shape == mask.shape == camera.shape == (width, height)
    # Banding is horizontal: constant along x, varying along y.
    assert np.all(dark == dark[:1, :])
    assert np.ptp(dark[0]) > fake_camera.BAND_AMPLITUDE
    # Saturated exactly where the numeral is, so the _sat map is its shape.
    np.testing.assert_array_equal(camera >= fake_camera.SATURATION, mask)
    # Elsewhere, subtracting the dark leaves only noise.
    residual = camera[~mask].astype(float) - dark[~mask]
    assert abs(residual.mean()) < 1
    # The 7's bar is across the top, so with y upward it is at high y.
    ys = mask.any(axis=0).nonzero()[0]
    assert mask[:, ys.max()].sum() > mask[:, ys.min()].sum()
