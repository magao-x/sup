"""Tests for the sun and moon rise/set endpoint.

Rise and set times are solved iteratively, which is slow, and they move by
minutes a day, which makes recomputing them per request pointless. The night
is the granularity the observers care about.
"""
import asyncio
import datetime

import orjson
import pytest

import sup.core as core
from sup.core import SupViews, observing_night


class CountingSite:
    """Stands in for the astroplan Observer, counting how often it is asked."""
    class _Result:
        def __init__(self, label):
            self.label = label

        def to_value(self, fmt):
            return self.label

    def __init__(self):
        self.calls = 0

    def _answer(self, label):
        self.calls += 1
        return self._Result(label)

    def moon_rise_time(self, when):
        return self._answer('moonrise')

    def moon_set_time(self, when):
        return self._answer('moonset')

    def sun_rise_time(self, when):
        return self._answer('sunrise')

    def sun_set_time(self, when):
        return self._answer('sunset')


@pytest.fixture
def site(monkeypatch):
    counting = CountingSite()
    monkeypatch.setattr(core, 'LCO_SITE', counting)
    return counting


def payload_of(response):
    return orjson.loads(response.body)


def test_one_night_is_computed_once(site, monkeypatch):
    async def scenario():
        views = SupViews(app=None)
        # Three moments spread across one night, including either side of UTC
        # midnight, which is the middle of the night here.
        moments = [
            datetime.datetime(2026, 10, 27, 23, tzinfo=datetime.timezone.utc),
            datetime.datetime(2026, 10, 28, 2, tzinfo=datetime.timezone.utc),
            datetime.datetime(2026, 10, 28, 8, tzinfo=datetime.timezone.utc),
        ]
        responses = []
        for moment in moments:
            monkeypatch.setattr(core, 'utc_now', lambda m=moment: m)
            responses.append(payload_of(await views.sun_and_moon(request=None)))

        assert site.calls == 4  # four quantities, computed once between them
        assert responses[0] == responses[1] == responses[2]
        assert responses[0]['solar_system']['sun']['rise'] == 'sunrise'
    asyncio.run(scenario())


def test_the_next_night_is_computed_afresh(site, monkeypatch):
    async def scenario():
        views = SupViews(app=None)
        tonight = datetime.datetime(2026, 10, 27, 23, tzinfo=datetime.timezone.utc)
        monkeypatch.setattr(core, 'utc_now', lambda: tonight)
        await views.sun_and_moon(request=None)
        assert site.calls == 4

        tomorrow = datetime.datetime(2026, 10, 28, 23, tzinfo=datetime.timezone.utc)
        monkeypatch.setattr(core, 'utc_now', lambda: tomorrow)
        await views.sun_and_moon(request=None)
        assert site.calls == 8
    asyncio.run(scenario())


def test_simultaneous_first_requests_compute_once(site, monkeypatch):
    async def scenario():
        views = SupViews(app=None)
        moment = datetime.datetime(2026, 10, 27, 23, tzinfo=datetime.timezone.utc)
        monkeypatch.setattr(core, 'utc_now', lambda: moment)
        # A night's first request often coincides with several others as
        # people open the page; they should share one computation.
        await asyncio.gather(*(views.sun_and_moon(request=None) for _ in range(5)))
        assert site.calls == 4
    asyncio.run(scenario())


def test_a_night_spanning_utc_midnight_has_one_key():
    evening = datetime.datetime(2026, 10, 27, 23, tzinfo=datetime.timezone.utc)
    after_midnight = datetime.datetime(2026, 10, 28, 6, tzinfo=datetime.timezone.utc)
    assert observing_night(evening) == observing_night(after_midnight)


def test_the_key_turns_over_around_local_noon():
    before_noon = datetime.datetime(2026, 10, 27, 16, tzinfo=datetime.timezone.utc)
    after_noon = datetime.datetime(2026, 10, 27, 17, tzinfo=datetime.timezone.utc)
    assert observing_night(before_noon) != observing_night(after_noon)
    # ...and not at a time anyone would be observing through.
    assert observing_night(
        datetime.datetime(2026, 10, 27, 3, tzinfo=datetime.timezone.utc)
    ) == observing_night(
        datetime.datetime(2026, 10, 27, 4, tzinfo=datetime.timezone.utc)
    )
