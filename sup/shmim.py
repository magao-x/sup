#!/usr/bin/env python
import blosc
import sys
import numpy as np
import time
import struct
from magpyx.utils import ImageStream

def shmim_grabber():
    tmp_dir = sys.argv[1]
    shmim_name = sys.argv[2]
    shmim = ImageStream(shmim_name)
    while True:
        frame = shmim.grab_latest().astype(np.uint16)
        frame_bytes = frame.tobytes()
        frame_compress = blosc.compress(frame_bytes, clevel=5, cname='lz4', shuffle=blosc.SHUFFLE, typesize=2)
        with open(f"{tmp_dir}/{shmim_name}.dat", "wb") as fh:
            fh.write(struct.pack("<I", frame.shape[0]))
            fh.write(struct.pack("<I", frame.shape[1]))
            fh.write(frame_compress)
        time.sleep(1)

if __name__ == "__main__":
    shmim_grabber()