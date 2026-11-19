"""Tests for finding the streams to list: from rtimv configs first, then
whatever else is in the shmim directory, but never a stream's dark or
saturation mask."""
import numpy as np
import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from sup import isio_mock, shmim
from sup.stream_catalog import StreamInfo, build_catalog, read_rtimv_config
from sup.streaming import ShmimHub, ShmimStreamingConfig


@pytest.fixture
def shm_dir(tmp_path, monkeypatch):
    path = tmp_path / "shm"
    path.mkdir()
    monkeypatch.setenv("MILK_SHM_DIR", str(path))
    monkeypatch.setattr(shmim, "ISIO", isio_mock)
    return path


@pytest.fixture
def config_dir(tmp_path):
    path = tmp_path / "config"
    path.mkdir()
    return path


def add_shmims(*names):
    for name in names:
        img = isio_mock.Image()
        assert img.create(name, np.zeros((2, 2), dtype=np.uint16)) == 0
        img.close()


def write_config(config_dir, filename, text):
    path = config_dir / filename
    path.write_text(text)
    return path


CAMWFS = """\
satLevel=16383
quality=80

[image]
key=camwfs

[dark]
key=camwfs_dark

[indi]
ipAddress=127.0.0.1
"""

DM00DISP = """\
autoscale=false
# the flat is the "dark"
[image]
key=dm00disp

[dark]
key=dm00disp00

[satMask]
key=dm00dispST
"""


def test_an_rtimv_config_gives_the_image_its_dark_mask_and_level(config_dir):
    assert read_rtimv_config(write_config(config_dir, "rtimv_camwfs.conf", CAMWFS)) == StreamInfo(
        name="camwfs", dark="camwfs_dark", sat_level=16383, config="rtimv_camwfs.conf")
    assert read_rtimv_config(write_config(config_dir, "rtimv_dm00disp.conf", DM00DISP)) == StreamInfo(
        name="dm00disp", dark="dm00disp00", sat_mask="dm00dispST", config="rtimv_dm00disp.conf")


def test_a_config_naming_no_image_defines_no_stream(config_dir):
    assert read_rtimv_config(write_config(config_dir, "rtimv_x.conf", "satLevel=1\n[dark]\nkey=x_dark\n")) is None


def test_configured_streams_come_first_and_darks_and_masks_are_left_out(config_dir, shm_dir):
    write_config(config_dir, "rtimv_dm00disp.conf", DM00DISP)
    write_config(config_dir, "rtimv_camwfs.conf", CAMWFS)
    write_config(config_dir, "rtimv_camngws.conf", "[image]\nkey=camngws\n")
    write_config(config_dir, "camwfs.conf", "[image]\nkey=notrtimv\n")
    add_shmims("acc000_psds", "camwfs", "camwfs_dark", "camwfs_avg", "dm00disp00", "dm00disp01", "dm00dispST")
    (shm_dir / "processinfo.list.shm").write_text("")
    catalog = build_catalog(config_dir)
    assert list(catalog.streams) == [
        # By config file name, whether or not their shmims exist yet...
        "camngws", "camwfs", "dm00disp",
        # ...then the rest by name.
        "acc000_psds", "camwfs_avg", "dm00disp01",
    ]
    assert catalog.streams["camwfs_avg"] == StreamInfo(name="camwfs_avg")
    assert catalog.excluded == {"camwfs_dark", "dm00disp00", "dm00dispST"}


def test_a_configured_stream_used_as_another_ones_dark_is_left_out(config_dir, shm_dir):
    write_config(config_dir, "rtimv_camwfs.conf", CAMWFS)
    write_config(config_dir, "rtimv_camwfs_dark.conf", "[image]\nkey=camwfs_dark\n")
    assert list(build_catalog(config_dir).streams) == ["camwfs"]


def test_the_first_config_for_a_stream_defines_it(config_dir, shm_dir):
    write_config(config_dir, "rtimv_a.conf", "satLevel=1\n[image]\nkey=cam\n")
    write_config(config_dir, "rtimv_b.conf", "satLevel=2\n[image]\nkey=cam\n")
    assert build_catalog(config_dir).streams["cam"].sat_level == 1


def test_either_source_may_be_missing(tmp_path, config_dir, shm_dir):
    add_shmims("camsim")
    write_config(config_dir, "rtimv_camwfs.conf", CAMWFS)
    assert list(build_catalog(tmp_path / "nowhere").streams) == ["camsim"]
    assert list(build_catalog(None).streams) == ["camsim"]
    assert list(build_catalog(config_dir, tmp_path / "nowhere").streams) == ["camwfs"]


def test_a_broken_config_is_skipped(config_dir, shm_dir):
    write_config(config_dir, "rtimv_bad.conf", "[image]\nkey=bad\nsatLevel\n")
    write_config(config_dir, "rtimv_camwfs.conf", CAMWFS)
    assert list(build_catalog(config_dir).streams) == ["camwfs"]


def test_the_catalog_is_served_beside_the_feeds(config_dir, shm_dir):
    write_config(config_dir, "rtimv_camwfs.conf", CAMWFS)
    add_shmims("camwfs", "camwfs_dark", "camtip")
    hub = ShmimHub(ShmimStreamingConfig(rtimv_config_dir=str(config_dir)))
    with TestClient(Starlette(routes=hub.routes())) as client:
        response = client.get("/ws/viewcam/")
    assert response.status_code == 200
    assert response.json() == {
        "streams": [
            {"name": "camwfs", "dark": "camwfs_dark", "sat_mask": None, "sat_level": 16383, "config": "rtimv_camwfs.conf"},
            {"name": "camtip", "dark": None, "sat_mask": None, "sat_level": None, "config": None},
        ],
        "excluded": ["camwfs_dark"],
    }
