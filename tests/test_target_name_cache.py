"""Tests for remembering target name lookups.

Resolving a name goes out to Sesame over the network. Positions and the
non-existence of a name are worth remembering; a failure to get any answer is
not, or one outage would make a real target unresolvable until restart.

These run astropy's real resolver with only the download replaced, because the
distinction between "no such object" and "no answer" rests on the wording of
astropy's errors, and these tests are what notice if that wording changes.
"""
import asyncio
import urllib.error

import pytest
from astropy.coordinates import name_resolve
from starlette.exceptions import HTTPException

import sup.core as core
from sup.core import SupViews, resolve_target_name

# What Sesame sends back for a name it knows, trimmed to the line that matters.
FOUND = "# M 31\n%J 10.68470833 +41.26875000 = 00:42:44.33 +41:16:07.5\n"
# What Sesame sends back for a name none of its databases know.
NOT_FOUND = "# nosuchthing\n#! *** Nothing found ***\n"


class FakeSesame:
    """Stands in for the network, counting how often it is asked."""
    def __init__(self, respond):
        self.respond = respond
        self.calls = 0

    def download_file(self, url, **kwargs):
        self.calls += 1
        return self.respond(url)


@pytest.fixture(autouse=True)
def empty_cache():
    resolve_target_name.cache_clear()
    yield
    resolve_target_name.cache_clear()


def install(monkeypatch, respond):
    sesame = FakeSesame(respond)
    monkeypatch.setattr(name_resolve, 'download_file', sesame.download_file)
    # download_file normally returns a path; ours returns the contents.
    monkeypatch.setattr(name_resolve, 'get_file_contents', lambda contents: contents)
    return sesame


def test_a_found_target_is_looked_up_once(monkeypatch):
    sesame = install(monkeypatch, lambda url: FOUND)
    first = resolve_target_name('M31')
    second = resolve_target_name('M31')
    assert sesame.calls == 1
    assert first.ra.deg == pytest.approx(10.68470833)
    assert second is first


def test_a_nonexistent_target_is_looked_up_once(monkeypatch):
    sesame = install(monkeypatch, lambda url: NOT_FOUND)
    assert resolve_target_name('nosuchthing') is None
    assert resolve_target_name('nosuchthing') is None
    assert sesame.calls == 1


def test_an_unreachable_service_is_asked_again(monkeypatch):
    def unreachable(url):
        raise urllib.error.URLError('connection refused')
    sesame = install(monkeypatch, unreachable)
    with pytest.raises(name_resolve.NameResolveError):
        resolve_target_name('M31')
    calls_after_first = sesame.calls

    sesame.respond = lambda url: FOUND
    assert resolve_target_name('M31') is not None
    assert sesame.calls > calls_after_first


def test_a_timeout_is_asked_again(monkeypatch):
    def too_slow(url):
        raise TimeoutError()
    sesame = install(monkeypatch, too_slow)
    with pytest.raises(name_resolve.NameResolveError):
        resolve_target_name('M31')
    calls_after_first = sesame.calls

    sesame.respond = lambda url: FOUND
    assert resolve_target_name('M31') is not None
    assert sesame.calls > calls_after_first


class Request:
    def __init__(self, **query_params):
        self.query_params = query_params


def test_the_endpoint_reports_an_unknown_name_as_not_found(monkeypatch):
    install(monkeypatch, lambda url: NOT_FOUND)
    views = SupViews(app=None)
    with pytest.raises(HTTPException) as caught:
        asyncio.run(views.observability_curves(Request(target_name='nosuchthing')))
    assert caught.value.status_code == 404


def test_the_endpoint_shares_lookups_across_spellings_with_whitespace(monkeypatch):
    sesame = install(monkeypatch, lambda url: FOUND)
    views = SupViews(app=None)
    asyncio.run(views.observability_curves(Request(target_name='M31')))
    asyncio.run(views.observability_curves(Request(target_name=' M31 ')))
    assert sesame.calls == 1
