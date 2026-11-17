"""Tests for the ImageStreamIOWrap stand-in.

What these pin down is the behaviour sup will lean on from the real binding:
pixels written by one Image are what another Image of the same name reads,
in the same column-major layout, and a reader waiting on a semaphore wakes
when a writer in another process writes.
"""
import asyncio
import datetime
import os
import subprocess
import sys
import threading
import time
import warnings

import numpy as np
import pytest

from sup import isio_mock as ISIO


@pytest.fixture(autouse=True)
def shm_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MILK_SHM_DIR", str(tmp_path))
    return tmp_path


def make_image(name="test", data=None, **kwargs):
    img = ISIO.Image()
    if data is None:
        data = np.arange(12, dtype=np.float32).reshape(3, 4)
    assert img.create(name, data, **kwargs) == 0
    return img


def test_round_trip_between_handles(shm_dir):
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    writer = make_image(data=data)
    assert (shm_dir / "test.im.mock").exists()

    reader = ISIO.Image()
    assert reader.open("test") == 0
    assert reader.shape == (3, 4)
    np.testing.assert_array_equal(np.array(reader), data)
    np.testing.assert_array_equal(reader.copy(), data)

    writer.write(np.ones((3, 4), dtype=np.float32))
    np.testing.assert_array_equal(np.array(reader), np.ones((3, 4)))


def test_layout_is_column_major_like_the_binding():
    img = make_image()
    assert np.array(img).flags.f_contiguous
    assert img.copy().flags.f_contiguous
    # A zero-copy view sees later writes.
    view = np.asarray(img)
    img.write(np.full((3, 4), 7, dtype=np.float32))
    assert view[0, 0] == 7


def test_metadata():
    before = datetime.datetime.now() - datetime.timedelta(seconds=1)
    img = make_image(data=np.zeros((5, 6, 2), dtype=np.uint16), NBsem=4, NBkw=3)
    md = img.md
    assert md.name == "test"
    assert md.version == "2.00"
    assert md.naxis == 3
    assert md.size == [5, 6, 2]
    assert md.nelement == 60
    assert md.datatype == ISIO.ImageStreamIODataType.UINT16
    assert md.datatype is ISIO.ImageStreamIODataType.Type.UINT16
    assert md.imagetype == ISIO.ImageStreamIOType.MATH_DATA_TYPE
    assert md.sem == 4
    assert md.NBkw == 3
    assert md.shared == 1
    assert md.location == -1
    assert md.location_str == "CPU RAM"
    assert md.creationtime >= before
    assert md.lastaccesstime >= md.creationtime
    assert md.cnt0 == 1  # create() writes the initial pixels
    assert img.used == 1
    assert img.memsize > 60 * 2
    assert img.semReadPID == [0, 0, 0, 0]
    assert "Name: test" in repr(md)


def test_metadata_is_live():
    writer = make_image()
    reader = ISIO.Image()
    reader.open("test")
    md = reader.md
    assert md.cnt0 == 1
    writer.write(np.zeros((3, 4), dtype=np.float32))
    writer.write(np.zeros((3, 4), dtype=np.float32))
    assert md.cnt0 == 3
    assert md.cnt1 == 3


def test_update_sets_times_and_posts():
    img = make_image(NBsem=1)
    img.semflush(-1)
    stamp = datetime.datetime(2026, 1, 2, 3, 4, 5, 678000)
    assert img.update_atime(stamp) == 0
    assert img.md.acqtime == stamp
    assert img.md.cnt0 == 2
    assert img.semvalue(0) == 1
    assert img.update() == 0
    assert img.md.writetime >= stamp


def test_write_rejects_mismatches():
    img = make_image()
    with pytest.raises(ValueError, match="incompatible type"):
        img.write(np.zeros((3, 4), dtype=np.float64))
    with pytest.raises(ValueError, match="incompatible number of axis"):
        img.write(np.zeros(12, dtype=np.float32))
    with pytest.raises(ValueError, match="incompatible shape"):
        img.write(np.zeros((4, 3), dtype=np.float32))


def test_create_rejects_what_the_binding_cannot_hold():
    img = ISIO.Image()
    with pytest.raises(RuntimeError, match="Not implemented datatype"):
        img.create("bad", np.zeros(3, dtype=np.float16))
    with pytest.raises(TypeError):
        img.create("bad", [1, 2, 3])
    with pytest.raises(NotImplementedError):
        img.create("bad", np.zeros(3, dtype=np.float32), location=0)
    assert img.create("bad", np.zeros((1, 1, 1, 1), dtype=np.float32)) == ISIO.IMAGESTREAMIO_INVALIDARG


def test_uninitialized_image():
    img = ISIO.Image()
    assert img.md is None
    assert img.used == 0
    with pytest.raises(RuntimeError, match="image not initialized"):
        img.shape
    with pytest.raises(RuntimeError, match="image not initialized"):
        img.semwait(0)
    assert img.open("missing") == ISIO.IMAGESTREAMIO_FILEOPEN


def test_open_rejects_foreign_files(shm_dir):
    (shm_dir / "junk.im.mock").write_bytes(b"\0" * 4096)
    assert ISIO.Image().open("junk") == ISIO.IMAGESTREAMIO_FILEOPEN


def test_close_and_destroy(shm_dir):
    img = make_image()
    view = np.asarray(img)  # an outstanding view must not stop close()
    assert img.close() == 0
    assert img.md is None
    assert view.shape == (3, 4)
    assert (shm_dir / "test.im.mock").exists()

    assert img.open("test") == 0
    assert img.destroy() == 0
    assert not (shm_dir / "test.im.mock").exists()


def test_recreate_leaves_open_readers_whole():
    make_image(data=np.zeros((3, 4), dtype=np.float32))
    reader = ISIO.Image()
    reader.open("test")
    make_image(data=np.ones((8, 8), dtype=np.int32))
    assert reader.shape == (3, 4)
    assert reader.open("test") == 0
    assert reader.shape == (8, 8)


def test_local_image_has_no_file(shm_dir):
    img = make_image(shared=0)
    assert img.memsize == 0
    assert not list(shm_dir.iterdir())
    img.write(np.zeros((3, 4), dtype=np.float32))
    assert img.md.cnt0 == 2


def test_keywords_round_trip():
    img = make_image(NBkw=4)
    img.set_kws({
        "EXPTIME": ISIO.Image_kw("EXPTIME", 0.25, "seconds"),
        "CAMERA": ISIO.Image_kw("CAMERA", "camwfs"),
        "FRAMENO": ISIO.Image_kw("FRAMENO", 42),
    })
    other = ISIO.Image()
    other.open("test")
    kws = other.get_kws()
    assert kws["EXPTIME"].type == "D"
    assert kws["EXPTIME"].value == 0.25
    assert kws["EXPTIME"].comment == "seconds"
    assert kws["CAMERA"].value == "camwfs"
    assert kws["FRAMENO"].type == "L"
    assert kws["FRAMENO"].value == 42
    # Sorted by name, as the binding's std::map leaves them.
    assert [kw.name for kw in other.get_kws_list()] == ["CAMERA", "EXPTIME", "FRAMENO"]
    assert str(kws["EXPTIME"]) == "0.25 seconds"

    img.set_kws_list([ISIO.Image_kw("ONLY", 1)])
    assert list(other.get_kws()) == ["ONLY"]
    with pytest.raises(RuntimeError, match="Too many keywords"):
        img.set_kws_list([ISIO.Image_kw(f"K{i}", i) for i in range(5)])


def test_keyword_validation():
    with pytest.raises(ValueError, match="name too long"):
        ISIO.Image_kw("X" * 17, 1)
    with pytest.raises(ValueError, match="valstr too long"):
        ISIO.Image_kw("X", "Y" * 17)
    assert ISIO.Image_kw("X", numf=1).type == "D"
    with pytest.raises(TypeError):
        ISIO.Image_kw("X", numl=1.5)
    with pytest.raises(RuntimeError, match="Unknown format"):
        ISIO.Image_kw().value


def test_semaphore_counting():
    img = make_image(NBsem=2)
    # create() posted once.
    assert img.semvalue(0) == 1
    for _ in range(20):
        img.sempost(-1)
    assert img.semvalue(0) == ISIO.SEMAPHORE_MAXVAL
    assert img.semtrywait(0) == 0
    assert img.semvalue(0) == ISIO.SEMAPHORE_MAXVAL - 1
    img.semflush(0)
    assert img.semvalue(0) == 0
    assert img.semvalue(1) == ISIO.SEMAPHORE_MAXVAL
    assert img.semtrywait(0) == -1
    assert img.semWritePID[0] == os.getpid()
    # Out of range, the binding reports rather than raises.
    assert img.semvalue(5) == -1
    assert img.semwait(5) == ISIO.EXIT_FAILURE


def test_semtimedwait_times_out():
    img = make_image(NBsem=1)
    img.semflush(-1)
    start = time.monotonic()
    assert img.semtimedwait(0, 0.05) == -1
    assert time.monotonic() - start >= 0.05


def test_getsemwaitindex():
    img = make_image(NBsem=3)
    assert img.getsemwaitindex(1) == 1
    assert img.semReadPID[1] == os.getpid()
    # The same process gets the same semaphore back whatever it asks for.
    assert img.getsemwaitindex(2) == 1

    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    img._sem_read_pid[:] = [dead.pid, dead.pid, dead.pid]
    assert img.getsemwaitindex(2) == 2


def test_waiter_in_a_thread_wakes_on_write():
    img = make_image(NBsem=1)
    index = img.getsemwaitindex(0)
    img.semflush(index)
    woke = []
    waiter = threading.Thread(target=lambda: woke.append(img.semtimedwait(index, 5)))
    with pytest.warns(ISIO.BlockingWaitWarning, match="off the main thread"):
        waiter.start()
        time.sleep(0.05)
        assert not woke
        writer = ISIO.Image()
        writer.open("test")
        writer.write(np.zeros((3, 4), dtype=np.float32))
        waiter.join()
    assert woke == [0]


def test_blocking_wait_in_event_loop_warns():
    img = make_image(NBsem=1)

    async def wait_in_loop():
        return img.semtimedwait(0, 0.01)

    with pytest.warns(ISIO.BlockingWaitWarning, match="event loop"):
        asyncio.run(wait_in_loop())


def test_waits_that_cannot_stall_others_do_not_warn():
    img = make_image(NBsem=1)

    async def poll_in_loop():
        return img.semtrywait(0), img.semtimedwait(0, 0)

    with warnings.catch_warnings():
        warnings.simplefilter("error", ISIO.BlockingWaitWarning)
        img.semtimedwait(0, 0.01)  # main thread, no loop
        asyncio.run(poll_in_loop())


WRITER_SCRIPT = """
import sys, time
import numpy as np
from sup import isio_mock as ISIO
img = ISIO.Image()
assert img.open("test") == 0
for i in range(int(sys.argv[1])):
    time.sleep(0.02)
    img.write(np.full((3, 4), i + 1, dtype=np.float32))
"""


def test_waiter_wakes_on_write_from_another_process(shm_dir):
    img = make_image()
    index = img.getsemwaitindex(0)
    img.semflush(index)
    frames = 5
    writer = subprocess.Popen(
        [sys.executable, "-c", WRITER_SCRIPT, str(frames)],
        env={**os.environ, "MILK_SHM_DIR": str(shm_dir)},
    )
    seen = []
    try:
        while len(seen) < frames:
            assert img.semtimedwait(index, 5) == 0
            seen.append(img.copy()[0, 0])
    finally:
        writer.wait(timeout=10)
    assert writer.returncode == 0
    assert seen[-1] == frames
    assert img.md.cnt0 == frames + 1
