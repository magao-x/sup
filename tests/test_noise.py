"""Tests for estimating a stream's noise from its frames."""
import numpy as np
import pytest

from sup.noise import NoiseModel, NoiseTracker, estimate_noise


def camera_frame(seed, bias=432.0, read_noise=14.0, noise_slope=8.0, shape=(256, 256)):
    """A camera frame: a bright blob over a bias, with read noise and photon
    noise growing with the signal."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[:shape[0], :shape[1]]
    truth = bias + 3000 * np.exp(-((x - shape[1] / 2) ** 2 + (y - shape[0] / 2) ** 2) / 2000)
    sigma = np.sqrt(read_noise ** 2 + noise_slope * (truth - bias))
    return np.clip(np.rint(truth + rng.normal(0, 1, shape) * sigma), 0, 65535).astype(np.uint16)


def test_a_camera_frames_noise_is_recovered():
    model = estimate_noise(camera_frame(0))
    # The bias is taken from the faint pixels, so a little under the true
    # one, and the fit is then a little low: the safe side, finer steps.
    assert 420 < model.bias <= 432
    assert 11 < model.read_noise < 16
    assert 6 < model.noise_slope < 10


def test_read_noise_alone_has_no_slope():
    rng = np.random.default_rng(1)
    shape = np.sin(np.linspace(0, 3, 50))[None, :] * np.cos(np.linspace(0, 2, 50))[:, None]
    model = estimate_noise(shape + rng.normal(0, 0.04, shape.shape))
    assert model.noise_slope == pytest.approx(0, abs=0.01)
    assert model.read_noise == pytest.approx(0.04, rel=0.2)


def test_real_structure_is_not_noise():
    # Sharp edges along each row: few pixels, so the robust fit ignores them.
    rng = np.random.default_rng(2)
    frame = 500 + rng.normal(0, 5, (128, 128))
    frame[:, 64:] += 2000
    model = estimate_noise(frame)
    assert model.read_noise == pytest.approx(5, rel=0.2)


@pytest.mark.parametrize("frame", [
    np.full((16, 16), 3.0),
    np.tile(np.arange(16.0), (16, 1)),   # a ramp along the rows: no residual
    np.zeros((16, 4)),                    # rows too short to look along
    np.arange(100.0),                     # one row: nothing to take levels from
    np.zeros(0),
])
def test_frames_without_noise_have_no_model(frame):
    assert estimate_noise(frame) is None


def test_the_tracker_refits_now_and_then_and_smooths():
    tracker = NoiseTracker(every=3, smoothing=0.5)
    first = tracker.update(camera_frame(0))
    # Until the next refit, the model holds, whatever the frames do.
    assert tracker.update(camera_frame(1, read_noise=40.0)) == first
    assert tracker.update(camera_frame(2, read_noise=40.0)) == first
    refit = tracker.update(camera_frame(3, read_noise=40.0))
    # Halfway towards the new frame's noise.
    assert first.read_noise < refit.read_noise < 35


def test_the_tracker_starts_over_on_a_new_shape():
    tracker = NoiseTracker(every=100)
    tracker.update(camera_frame(0))
    small = tracker.update(camera_frame(1, read_noise=40.0, shape=(64, 64)))
    assert small.read_noise > 25
    assert isinstance(small, NoiseModel)
