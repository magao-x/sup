#!/usr/bin/env python
import asyncio
import blosc
import sys
import numpy as np
import time
import struct
import pathlib
import configparser
from magpyx.utils import ImageStream
import ImageStreamIOWrap
import logging

log = logging.getLogger(__name__)

from .constants import CONFIG_PATH, TMPFILE_ROOT

DataType = ImageStreamIOWrap.ImageStreamIODataType

INTEGER_TYPES = (DataType.UINT8, DataType.INT8, DataType.UINT16, DataType.INT16, DataType.UINT32, DataType.INT32, DataType.UINT64, DataType.INT64)
FLOAT_TYPES = (DataType.HALF, DataType.FLOAT, DataType.DOUBLE)


def parse_rtimv_config(config_path : pathlib.Path):
    cp = configparser.ConfigParser()
    # handle leading section-less values
    with open(config_path, 'r') as fh:
        cp.read_string('[default]\n' + fh.read())
    shmim_name = cp.get('image', 'key')
    dark_name = cp.get('dark', 'key', fallback=None)
    return shmim_name, dark_name

def shmim_grabber():
    tmp_dir = sys.argv[1]
    shmim_name = sys.argv[2]
    if len(sys.argv) > 3:
        dark_name = sys.argv[3]
        dark_shmim = ImageStream(dark_name)
    else:
        dark_shmim = None
    shmim = ImageStream(shmim_name)
    while True:
        frame = shmim.grab_latest()
        if shmim.md.datatype in INTEGER_TYPES:
            cast_type = np.int32
        elif shmim.md.datatype in FLOAT_TYPES:
            cast_type = np.float32
        else:
            raise RuntimeError(f"Unsupported data type: {frame.md.datatype}")
        frame = frame.astype(cast_type)
        if dark_shmim is not None:
            dark_frame = dark_shmim.grab_latest().astype(cast_type)
            if frame.shape != dark_frame.shape:
                print(f"[{shmim_name}] {frame.shape=} [{dark_name}] {dark_frame.shape=}")
            else:
                frame = frame - dark_frame
        frame_bytes = frame.tobytes()
        frame_compress = blosc.compress(frame_bytes, clevel=5, cname='lz4', shuffle=blosc.SHUFFLE, typesize=2)
        with open(f"{tmp_dir}/{shmim_name}.blosc.lz4", "wb") as fh:
            fh.write(struct.pack("<I", frame.shape[0]))
            fh.write(struct.pack("<I", frame.shape[1]))
            fh.write(struct.pack("c", b'i' if cast_type is np.int32 else b'f'))
            fh.write(frame_compress)
        time.sleep(1)

async def launch_camera_watcher(camera):
    print(camera)
    cam_config = CONFIG_PATH / f'rtimv_{camera}.conf'
    im_name, dark_name = parse_rtimv_config(cam_config)
    args = [
        sys.executable,
        '-m',
        'sup.shmim',
        TMPFILE_ROOT.as_posix(),
        im_name,
    ]
    if dark_name is not None:
        args.append(dark_name)
    while True:
        cmd = ' '.join(args)
        log.debug(f"Launched {cmd!r}")
        proc = await asyncio.create_subprocess_exec(
            *args
        )
        await proc.wait()
        if proc.returncode > 0:
            log.debug(f'[{cmd!r} exited with {proc.returncode}]')
            await asyncio.sleep(60)
        await asyncio.sleep(1)

def shmim_coordinator():
    from .core import CONFIG

    logging.basicConfig(level='DEBUG')
    loop = asyncio.get_event_loop()
    tasks = set()
    for cam in CONFIG["config"]["replicated_cameras"]:
        tasks.add(loop.create_task(launch_camera_watcher(cam)))
    loop.run_until_complete(asyncio.wait(tasks))

if __name__ == "__main__":
    shmim_grabber()