"""Tests for the log history a browser is sent when it connects.

The viewer filters by level, so the history is kept per level: a flood at one
level must not leave a viewer filtered to another with nothing to show. And
because a browser gets the history and then every later batch, each message
must be in exactly one of the two at any moment, or it shows up twice or not
at all.
"""
import asyncio
import datetime

import orjson
from purepyindi2 import messages

from sup.core import INDIUpdateBatcher, LogHistory, SupWebSocket, WebInterface


def message(text, device='dev'):
    return messages.Message(
        message=text, device=device,
        timestamp=datetime.datetime(2026, 10, 28, tzinfo=datetime.timezone.utc),
    )


def texts(history):
    return [m.message for m in history.messages()]


def test_a_flood_at_one_level_keeps_the_others():
    history = LogHistory(per_level=3)
    history.add(message('ERR  the only error'))
    for i in range(50):
        history.add(message(f'INFO chatter {i}'))
    assert texts(history) == [
        'ERR  the only error', 'INFO chatter 47', 'INFO chatter 48', 'INFO chatter 49',
    ]


def test_levels_are_interleaved_in_the_order_they_arrived():
    history = LogHistory(per_level=10)
    for text in ['INFO a', 'WARN b', 'INFO c', 'ERR  d', 'NOTE e', 'WARN f']:
        history.add(message(text))
    assert texts(history) == ['INFO a', 'WARN b', 'INFO c', 'ERR  d', 'NOTE e', 'WARN f']


def test_messages_naming_no_level_are_not_kept():
    history = LogHistory(per_level=10)
    history.add(message('no level here'))
    history.add(message('DBUG not one of ours'))
    history.add(message('INFO kept'))
    assert texts(history) == ['INFO kept']


class FakeIndiClient:
    status = None

    def to_serializable(self):
        return {'devices': {}}


def test_messages_join_the_history_only_as_their_batch_goes_out():
    async def scenario():
        history = LogHistory(per_level=10)
        batcher = INDIUpdateBatcher(FakeIndiClient(), history)
        await batcher.process_update(message('INFO pending'))
        # Not yet broadcast, so a browser connecting now gets it in the next
        # batch; were it also in the history, it would see it twice.
        assert texts(history) == []
        batch = await batcher.generate_batch()
        assert [m.message for m in batch['logs']] == ['INFO pending']
        assert texts(history) == ['INFO pending']
        # And it isn't sent again.
        assert (await batcher.generate_batch())['logs'] == []
    asyncio.run(scenario())


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def accept(self):
        pass

    async def send_bytes(self, payload):
        self.sent.append(orjson.loads(payload))


def test_a_connecting_browser_is_sent_the_history_after_the_snapshot():
    async def scenario():
        app = WebInterface()
        app.log_history_per_level = 2
        app.log_history = LogHistory(app.log_history_per_level)
        app.indi_client = FakeIndiClient()
        for text in ['ERR  e1', 'INFO i1', 'INFO i2', 'INFO i3']:
            app.log_history.add(message(text))

        endpoint = SupWebSocket.__new__(SupWebSocket)
        endpoint.cli = app
        ws = FakeWebSocket()
        await endpoint.on_connect(ws)
        await asyncio.sleep(0.05)  # let the client's sender drain its queue

        actions = [m['action'] for m in ws.sent]
        assert actions.index('indi_init') < actions.index('log_history')
        history = ws.sent[actions.index('log_history')]['payload']
        assert history['per_level'] == 2
        assert [m['message'] for m in history['logs']] == ['ERR  e1', 'INFO i2', 'INFO i3']
        assert history['logs'][0]['device'] == 'dev'
        app.unregister_client(ws)
    asyncio.run(scenario())
