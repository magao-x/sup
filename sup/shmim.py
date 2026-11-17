"""Following shmim image streams from inside sup's event loop.

The ImageStreamIOWrap binding holds the GIL through semwait() and
semtimedwait(), so a blocking wait anywhere in this process (event loop or
worker thread) would stall all of sup until a frame arrived. Instead,
ShmimPoller only ever makes calls that return at once: it checks each
stream's frame counter (md.cnt0, a read of shared memory) every few
milliseconds and copies the frame when it moves. Display streams don't need
every frame of a kHz camera anyway, so it can also hold to a maximum rate.

Companion streams such as <name>_dark are ordinary shmims; follow them with
their own poller.
"""
import asyncio
import logging
import time

log = logging.getLogger(__name__)

try:
    import ImageStreamIOWrap as ISIO
except ImportError:
    from . import isio_mock as ISIO
    log.warning("ImageStreamIOWrap is not installed; shmims will come from sup.isio_mock")


class ShmimPoller:
    """Yields the new frames of one shmim, opening it once it exists and
    reopening it when it is recreated under the same name, which is what
    happens when a camera restarts or changes its region of interest.

    Use it as ``async for cnt0, frame in ShmimPoller("camwfs").frames():``;
    leaving the loop closes the stream.
    """
    def __init__(self, name, poll_interval=0.005, min_frame_interval=0.0, reopen_interval=1.0):
        self.name = name
        self.poll_interval = poll_interval
        self.min_frame_interval = min_frame_interval
        self.reopen_interval = reopen_interval

    def _open(self):
        img = ISIO.Image()
        if img.open(self.name) != 0:
            return None
        return img

    def exists(self):
        """Whether the shmim can be opened right now."""
        img = self._open()
        if img is None:
            return False
        img.close()
        return True

    def _replaced(self, img):
        """Whether a different image now has our name. One that is simply
        gone is not replaced: the mapping we hold stays valid, and following
        it until a successor appears costs nothing."""
        latest = self._open()
        if latest is None:
            return False
        try:
            return latest.md.inode != img.md.inode
        finally:
            latest.close()

    @staticmethod
    def _read(img):
        """Copy the frame, or return None if a write may have torn it.

        The writer sets md.write for the duration of its copy and bumps cnt0
        after, so a copy taken while neither moved is whole.
        """
        md = img.md
        before = md.cnt0
        if md.write:
            return None
        frame = img.copy()
        if md.write or md.cnt0 != before:
            return None
        return before, frame

    async def frames(self):
        img = None
        last_cnt0 = None
        last_yield = float("-inf")
        next_reopen_check = 0.0
        try:
            while True:
                now = time.monotonic()
                if img is None:
                    img = self._open()
                    if img is None:
                        await asyncio.sleep(self.reopen_interval)
                        continue
                    log.debug(f"Opened shmim {self.name} with shape {img.shape}")
                    last_cnt0 = None
                    next_reopen_check = now + self.reopen_interval
                elif now >= next_reopen_check:
                    next_reopen_check = now + self.reopen_interval
                    if self._replaced(img):
                        log.debug(f"Shmim {self.name} was recreated; reopening")
                        img.close()
                        img = None
                        continue
                if img.md.cnt0 != last_cnt0 and now - last_yield >= self.min_frame_interval:
                    result = self._read(img)
                    if result is not None:
                        last_cnt0, frame = result
                        last_yield = now
                        yield last_cnt0, frame
                await asyncio.sleep(self.poll_interval)
        finally:
            if img is not None:
                img.close()
