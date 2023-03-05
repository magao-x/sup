import argparse
import asyncio
import json
import logging
import os
import platform
import ssl

from starlette.responses import FileResponse

from starlette.routing import Route
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender

from magpyx.utils import ImageStream

from .utils import OrjsonResponse

ROOT = os.path.dirname(__file__)

ACTIVE_PEERCONNECTIONS = set()

async def video(request):
    return FileResponse(os.path.join(ROOT, "video.html"))


async def send_frames_task(channel):
    while True:
        arr = cam.grab_latest()
        channel.send(bytes(arr))
        await asyncio.sleep(5)


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    ACTIVE_PEERCONNECTIONS.add(pc)

    loop = asyncio.get_event_loop()

    background_tasks_per_pc = set()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            for task in background_tasks_per_pc:
                task.cancel()
            await pc.close()
            ACTIVE_PEERCONNECTIONS.discard(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print(message)
            channel.send(bytes(example_im))
        background_tasks_per_pc.add(loop.create_task(send_frames_task(channel)))


    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return OrjsonResponse(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    ACTIVE_PEERCONNECTIONS.clear()

ROUTES = [
    Route('/video', endpoint=video, methods=["GET", "POST"]),
    Route('/offer', endpoint=offer, methods=["GET", "POST"]),
    # TODO grab full frame on request for js9 inspector
]
