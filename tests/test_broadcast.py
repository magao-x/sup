"""Tests for fanning updates out to connected browsers.

The property worth protecting is that one slow client costs only itself.
Updates used to be awaited client by client, so a browser that had stopped
draining delayed delivery to every other browser and held up the next batch
as well --- and because the batcher keeps accumulating while a broadcast
waits, the next batch was then bigger and slower still.
"""
import asyncio

import pytest

from sup.core import WebInterface, WebSocketClient


class FakeWebSocket:
    """A websocket that can be made to stop draining, as a real one can."""
    def __init__(self, stalled=False):
        self.sent = []
        self.closed = False
        self.stalled = stalled
        self._released = asyncio.Event()

    async def send_bytes(self, payload):
        if self.stalled:
            await self._released.wait()
        self.sent.append(payload)

    async def close(self):
        self.closed = True

    def resume(self):
        self.stalled = False
        self._released.set()


def run(coro):
    return asyncio.run(coro)


def make_interface(max_pending=4):
    app = WebInterface()
    app.max_pending_updates_per_client = max_pending
    app.slow_send_warning_sec = 1000  # not under test; keep the log quiet
    return app


def test_a_stalled_client_does_not_delay_the_others():
    async def scenario():
        app = make_interface()
        stalled, healthy = FakeWebSocket(stalled=True), FakeWebSocket()
        app.register_client(stalled)
        app.register_client(healthy)

        app.broadcast(b'update')
        await asyncio.sleep(0.05)

        # The healthy client has it; the stalled one is still stuck on its own
        # send and has held nobody up.
        assert healthy.sent == [b'update']
        assert stalled.sent == []

        stalled.resume()
        await asyncio.sleep(0.05)
        assert stalled.sent == [b'update']
    run(scenario())


def test_broadcasting_does_not_wait_on_anyone():
    async def scenario():
        app = make_interface()
        app.register_client(FakeWebSocket(stalled=True))
        loop = asyncio.get_running_loop()
        before = loop.time()
        app.broadcast(b'update')
        # Enqueueing is the whole of the work; nothing here may block on I/O.
        assert loop.time() - before < 0.01
    run(scenario())


def test_updates_reach_a_client_in_order():
    async def scenario():
        app = make_interface()
        websocket = FakeWebSocket()
        app.register_client(websocket)
        for i in range(4):
            app.broadcast(f'update-{i}'.encode())
        await asyncio.sleep(0.05)
        assert websocket.sent == [b'update-0', b'update-1', b'update-2', b'update-3']
    run(scenario())


def test_a_client_that_never_drains_is_disconnected_rather_than_queued_forever():
    async def scenario():
        app = make_interface(max_pending=4)
        websocket = FakeWebSocket(stalled=True)
        client = app.register_client(websocket)

        for i in range(20):
            app.broadcast(f'update-{i}'.encode())
        await asyncio.sleep(0.05)

        # Dropped instead of accumulating a backlog that can only grow. The
        # frontend reconnects by itself and is sent a fresh snapshot, so this
        # costs that client a resync rather than any state.
        assert client.overflowed
        assert websocket.closed
        assert client.outbound.qsize() <= 4
    run(scenario())


def test_a_disconnected_client_stops_receiving():
    async def scenario():
        app = make_interface()
        websocket = FakeWebSocket()
        client = app.register_client(websocket)
        app.unregister_client(websocket)

        app.broadcast(b'update')
        await asyncio.sleep(0.05)
        assert websocket.sent == []
        assert client.sender is None
        assert app._connected_clients == []
    run(scenario())


def test_one_client_failing_to_send_does_not_affect_another():
    class BrokenWebSocket(FakeWebSocket):
        async def send_bytes(self, payload):
            raise ConnectionResetError("client vanished")

    async def scenario():
        app = make_interface()
        broken, healthy = BrokenWebSocket(), FakeWebSocket()
        app.register_client(broken)
        app.register_client(healthy)

        app.broadcast(b'update')
        await asyncio.sleep(0.05)
        assert healthy.sent == [b'update']
    run(scenario())
