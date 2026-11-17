#!/usr/bin/env python
"""A stand-in for a MagAO-X camera, for developing sup's image streaming
without an instrument. It writes three shmims, the way a camera and its
calibrations appear on the real system:

    <name>        the frames: a numeral, 0 through 9 and around again, over
                  the dark pattern and a little noise
    <name>_dark   the dark to subtract before display: a bias with
                  horizontal banding, written once
    <name>_sat    the saturation map, 1 where the frame is saturated, which
                  is exactly the numeral's pixels

Run it alongside sup; both default to the same shmim directory::

    python tests/fake_camera.py --name camsim --rate 2 --width 128 --height 128

On a Mac these are sup.isio_mock files. Where ImageStreamIOWrap is installed
they are real shmims, visible to milk tools and rtimv.

Arrays are indexed [x, y] like the real streams (md.size is [width, height]),
and the numeral reads upright with the origin at lower left, as rtimv and
DS9 show it.
"""
import argparse
import itertools
import time

import numpy as np

from sup.shmim import ISIO

# 5x7 glyphs, top row first.
GLYPHS = {
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
}
GLYPH_WIDTH, GLYPH_HEIGHT = 5, 7

# A 14-bit detector read into uint16, like most of the MagAO-X cameras.
SATURATION = 2**14 - 1
BIAS = 500.0
BAND_AMPLITUDE = 40.0
BAND_PERIOD = 16
READ_NOISE = 8.0


def numeral_mask(digit, width, height):
    """The numeral as a boolean [x, y] array, scaled to fill most of the frame."""
    glyph = np.array([[c == "#" for c in row] for row in GLYPHS[digit]])
    # Leave a glyph-pixel of margin all round.
    scale = max(1, min(width // (GLYPH_WIDTH + 2), height // (GLYPH_HEIGHT + 2)))
    glyph = np.kron(glyph, np.ones((scale, scale), dtype=bool))
    rows = np.zeros((height, width), dtype=bool)
    gh, gw = glyph.shape
    top, left = (height - gh) // 2, (width - gw) // 2
    rows[top:top + gh, left:left + gw] = glyph[:height - top, :width - left]
    # Rows run top to bottom; y runs bottom to top.
    return rows[::-1].T


def dark_frame(width, height, rng):
    """Bias plus banding that is constant along x and varies along y."""
    y = np.arange(height)
    bands = BAND_AMPLITUDE * np.sin(2 * np.pi * y / BAND_PERIOD)
    bands += rng.normal(0, BAND_AMPLITUDE / 4, height)  # some row-to-row jitter
    return np.broadcast_to(BIAS + bands, (width, height)).astype(np.uint16)


def camera_frame(mask, dark, rng):
    frame = dark + rng.normal(0, READ_NOISE, dark.shape)
    frame[mask] = SATURATION
    return np.clip(np.rint(frame), 0, SATURATION).astype(np.uint16)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", default="camsim", help="shmim name (default: %(default)s)")
    parser.add_argument("--rate", type=float, default=2.0, help="frames per second (default: %(default)s)")
    parser.add_argument("--width", type=int, default=128, help="frame width in pixels (default: %(default)s)")
    parser.add_argument("--height", type=int, default=128, help="frame height in pixels (default: %(default)s)")
    parser.add_argument("--frames", type=int, default=None, help="stop after this many frames (default: run forever)")
    args = parser.parse_args()

    rng = np.random.default_rng(0)
    dark = dark_frame(args.width, args.height, rng)
    blank = np.zeros((args.width, args.height), dtype=bool)

    cam, dark_img, sat = ISIO.Image(), ISIO.Image(), ISIO.Image()
    for img, name, data in (
        (dark_img, f"{args.name}_dark", dark),
        (sat, f"{args.name}_sat", blank.astype(np.uint8)),
        (cam, args.name, camera_frame(blank, dark, rng)),
    ):
        if img.create(name, data) != 0:
            raise SystemExit(f"Could not create shmim {name}")
    print(f"Writing {args.name}, {args.name}_dark and {args.name}_sat "
          f"at {args.width}x{args.height}, {args.rate} Hz")

    period = 1.0 / args.rate
    next_frame = time.monotonic()
    digits = itertools.cycle("0123456789")
    try:
        for count in itertools.count():
            if args.frames is not None and count >= args.frames:
                break
            mask = numeral_mask(next(digits), args.width, args.height)
            frame = camera_frame(mask, dark, rng)
            sat.write((frame >= SATURATION).astype(np.uint8))
            cam.write(frame)
            next_frame += period
            time.sleep(max(0.0, next_frame - time.monotonic()))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
