"""Tests for the endpoint that serves audible alert clips to the browser.

The contract these pin down is the one the browser player leans on: a clip URL
always means the same audio and may be cached forever, except under temp/,
where the device puts speech it synthesized for a one-off substituted string.
"""
import wave

import pytest
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from sup.core import SupViews


def write_silent_wav(path, frames=256):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(22050)
        handle.writeframes(b'\x00\x00' * frames)


class StubWebInterface:
    """Just the attributes the view reads, so the test needs no INDI server."""
    def __init__(self, cache_root):
        self.audible_alerts_cache_root = str(cache_root)


@pytest.fixture
def cache_root(tmp_path):
    root = tmp_path / "audibleAlerts_cache"
    write_silent_wav(root / "a1b2c3d4e5.wav")
    write_silent_wav(root / "walkup_example.wav")
    write_silent_wav(root / "temp" / "f6e5d4c3b2.wav")
    write_silent_wav(root / "nested" / "in a subdir.wav")
    # Something sensitive-looking next door, for the traversal check to aim at.
    (tmp_path / "secret.txt").write_text("not yours")
    return root


@pytest.fixture
def client(cache_root):
    views = SupViews(StubWebInterface(cache_root))
    app = Starlette(routes=[
        Route('/audible-alerts/clip/{path:path}', endpoint=views.audible_alerts_clip),
    ])
    return TestClient(app)


def test_serves_a_clip_as_wav(client):
    response = client.get('/audible-alerts/clip/a1b2c3d4e5.wav')
    assert response.status_code == 200
    # Explicitly audio/wav, not the platform table's audio/x-wav, which Safari
    # is fussier about.
    assert response.headers['content-type'] == 'audio/wav'
    assert response.content.startswith(b'RIFF')


def test_content_addressed_clips_are_cacheable_forever(client):
    response = client.get('/audible-alerts/clip/a1b2c3d4e5.wav')
    cache_control = response.headers['cache-control']
    assert 'immutable' in cache_control
    assert 'max-age=31536000' in cache_control


def test_substituted_speech_is_not_promised_to_last(client):
    # temp/ holds one-off synthesis that the device deletes when it restarts,
    # so those URLs must not claim to be good forever.
    response = client.get('/audible-alerts/clip/temp/f6e5d4c3b2.wav')
    assert response.status_code == 200
    assert 'immutable' not in response.headers['cache-control']
    assert response.headers['cache-control'] == 'public, max-age=300'


def test_revalidation_is_answered_without_resending_audio(client):
    first = client.get('/audible-alerts/clip/a1b2c3d4e5.wav')
    etag = first.headers['etag']
    second = client.get('/audible-alerts/clip/a1b2c3d4e5.wav',
                        headers={'If-None-Match': etag})
    assert second.status_code == 304
    assert second.content == b''
    assert second.headers['cache-control'] == first.headers['cache-control']


def test_stale_validator_gets_the_audio(client):
    response = client.get('/audible-alerts/clip/a1b2c3d4e5.wav',
                          headers={'If-None-Match': '"stale"'})
    assert response.status_code == 200
    assert response.content.startswith(b'RIFF')


def test_clip_names_may_contain_spaces(client):
    response = client.get('/audible-alerts/clip/nested/in%20a%20subdir.wav')
    assert response.status_code == 200


@pytest.mark.parametrize('path', [
    '../secret.txt',
    '../../etc/passwd',
    'nested/../../secret.txt',
])
def test_refuses_to_escape_the_cache_directory(client, path):
    assert client.get(f'/audible-alerts/clip/{path}').status_code == 404


def test_missing_clip_is_not_found(client):
    assert client.get('/audible-alerts/clip/nope.wav').status_code == 404


def test_directories_are_not_served(client):
    assert client.get('/audible-alerts/clip/temp').status_code == 404


def test_absent_cache_directory_is_not_an_error(tmp_path):
    # The device may simply not be running; that is a 404, not a 500.
    views = SupViews(StubWebInterface(tmp_path / "never_created"))
    app = Starlette(routes=[
        Route('/audible-alerts/clip/{path:path}', endpoint=views.audible_alerts_clip),
    ])
    assert TestClient(app).get('/audible-alerts/clip/a1b2c3d4e5.wav').status_code == 404
