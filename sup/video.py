import numpy as np
import asyncio
import ujson
import cv2

from starlette.routing import Route
from starlette.responses import UJSONResponse

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from av import VideoFrame



class FlagVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        height, width = 480, 640

        nframes = 30
        image_cube = np.zeros((nframes, height, width))
        yy, xx = np.indices((height, width))
        for idx in range(nframes):
            image_cube[idx] = np.cos((((1 + idx) * xx) / width) * 2 * np.pi)

        # generate flag
        data_bgr = np.hstack(
            [
                self._create_rectangle(
                    width=213, height=480, color=(255, 0, 0)
                ),  # blue
                self._create_rectangle(
                    width=214, height=480, color=(255, 255, 255)
                ),  # white
                self._create_rectangle(width=213, height=480, color=(0, 0, 255)),  # red
            ]
        )

        # shrink and center it
        M = np.float32([[0.5, 0, width / 4], [0, 0.5, height / 4]])
        data_bgr = cv2.warpAffine(data_bgr, M, (width, height))

        # compute animation
        omega = 2 * np.pi / height
        id_x = np.tile(np.array(range(width), dtype=np.float32), (height, 1))
        id_y = np.tile(
            np.array(range(height), dtype=np.float32), (width, 1)
        ).transpose()

        self.frames = []
        for k in range(30):
            phase = 2 * k * np.pi / 30
            map_x = id_x + 10 * np.cos(omega * id_x + phase)
            map_y = id_y + 10 * np.sin(omega * id_x + phase)
            self.frames.append(
                VideoFrame.from_ndarray(
                    cv2.remap(data_bgr, map_x, map_y, cv2.INTER_LINEAR), format="bgr24"
                )
            )

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.frames[self.counter % 30]
        frame.pts = pts
        frame.time_base = time_base
        self.counter += 1
        return frame

    def _create_rectangle(self, width, height, color):
        data_bgr = np.zeros((height, width, 3), np.uint8)
        data_bgr[:, :] = color
        return data_bgr


async def offer(request):
    params = await request.json()
    from pprint import pprint
    pprint(params)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    ACTIVE_PEERCONNECTIONS.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state is %s" % pc.iceConnectionState)
        # if pc.iceConnectionState == "failed":
        #     await pc.close()
        #     ACTIVE_PEERCONNECTIONS.discard(pc)

    await pc.setRemoteDescription(offer)
    # options = {"framerate": "30", "video_size": "640x480"}
    # player = MediaPlayer("default:none", format="avfoundation", options=options)
    # for t in pc.getTransceivers():
    #     if t.kind == "audio" and player.audio:
    #         pc.addTrack(player.audio)
    #     elif t.kind == "video" and player.video:
    #         pc.addTrack(player.video)

    for t in pc.getTransceivers():
        pprint(t.kind)
        if t.kind == "video":
            pc.addTrack(FlagVideoStreamTrack())
            print('added')
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return UJSONResponse(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        )


ACTIVE_PEERCONNECTIONS = set()

ROUTES = [
    Route('/offer', endpoint=offer, methods=["GET", "POST"]),
    # TODO grab full frame on request for js9 inspector
]
