"""Estimating a stream's noise, live, so its frames can be rounded to it.

The model is the one the viewcam protocol quantizes with (PROTOCOL.md,
"Quantization"): a pixel at ``value`` has noise variance ``read_noise**2 +
noise_slope * max(value - bias, 0)``. That is read noise alone where
``noise_slope`` is 0, and photon noise growing with the signal on top of it,
as for a camera (an EMCCD's gain makes the slope large).

It is fitted to each frame on its own, from how far each pixel strays from
what its neighbours along a row predict (a cubic through the two on either
side, so the image's own curvature doesn't count as noise). Pixels are
binned by level, each bin's variance taken robustly from the residuals (so
edges and other real structure barely count), and a line fitted to variance
against level. The level is taken from the pixel in the next row, which
plays no part in the residual: binning by any pixel the residual involves
would pick out its noise too, and narrow or widen the residuals depending on
what the image does nearby.
Comparing consecutive frames instead would count anything that really
changed between them, such as a deformable mirror's motion or a wavefront
sensor's vibration, as noise, and round it away.
"""
import dataclasses

import numpy as np

# The median absolute deviation of a normal distribution, in sigmas.
MAD_PER_SIGMA = 0.6744897501960817
# The cubic through x[i-2], x[i-1], x[i+1] and x[i+2] predicts x[i] as
# (4 (x[i-1] + x[i+1]) - x[i-2] - x[i+2]) / 6, whose own noise adds 34/36 of
# a pixel's variance to the residual.
RESIDUAL_VARIANCE = 1 + 34 / 36


@dataclasses.dataclass(frozen=True)
class NoiseModel:
    bias : float
    read_noise : float
    noise_slope : float


def estimate_noise(frame, max_samples=65536, bins=16, bias_percentile=10):
    """The noise model that best explains how a frame's pixels stray from
    their neighbours along its last axis, or None if they don't measurably
    (a frame of one value, or of noiseless bands) or it hasn't the two rows
    of five it takes. Looks at no more than about ``max_samples`` pixels."""
    rows = np.asarray(frame, dtype=np.float64)
    if rows.ndim == 0 or rows.shape[-1] < 5 or rows.size < 2 * rows.shape[-1]:
        return None
    rows = rows.reshape(-1, rows.shape[-1])
    # Every other row: each pair's first row gives the residuals, its second the levels.
    pairs = rows[: len(rows) // 2 * 2].reshape(-1, 2, rows.shape[-1])
    pairs = pairs[::max(1, pairs.size // max_samples)]
    here, below = pairs[:, 0], pairs[:, 1]
    predicted = (4 * (here[:, 1:-3] + here[:, 3:-1]) - here[:, :-4] - here[:, 4:]) / 6
    residual = (here[:, 2:-2] - predicted).ravel()
    level = below[:, 2:-2].ravel()
    finite = np.isfinite(residual)
    level, residual = level[finite], residual[finite]
    if level.size < 2 * bins:
        return None
    bias = float(np.percentile(level, bias_percentile))
    signals, variances = [], []
    for group in np.array_split(np.argsort(level), bins):
        r = residual[group]
        mad = np.median(np.abs(r - np.median(r)))
        if mad > 0:
            signals.append(np.mean(np.maximum(level[group] - bias, 0)))
            variances.append((mad / MAD_PER_SIGMA) ** 2 / RESIDUAL_VARIANCE)
    if not variances:
        return None
    signals, variances = np.array(signals), np.array(variances)
    slope, intercept = 0.0, float(np.median(variances))
    if len(variances) >= 2 and np.ptp(signals) > 0:
        slope, intercept = (float(v) for v in np.polyfit(signals, variances, 1))
    if slope <= 0:
        slope, intercept = 0.0, float(np.median(variances))
    if intercept <= 0:
        # The line runs below zero at the bias: take the faintest bin's noise.
        intercept = float(variances[np.argmin(signals)])
    return NoiseModel(bias=bias, read_noise=float(np.sqrt(intercept)), noise_slope=slope)


class NoiseTracker:
    """A stream's noise model, refitted every ``every`` frames and smoothed
    over refits, so that it neither costs a fit per frame nor swings with
    one odd frame. It starts over when the frames change shape or type."""
    def __init__(self, every=5, smoothing=0.3):
        self.every = every
        self.smoothing = smoothing
        self.model = None
        self._layout = None
        self._count = 0

    def update(self, frame):
        """Take the next frame; returns the current model, or None if the
        stream doesn't measurably vary."""
        layout = (frame.shape, frame.dtype)
        if layout != self._layout:
            self._layout, self.model, self._count = layout, None, 0
        self._count += 1
        if self._count > 1 and (self._count - 1) % self.every:
            return self.model
        fitted = estimate_noise(frame)
        if fitted is None or self.model is None:
            self.model = fitted
        else:
            mix = lambda old, new: (1 - self.smoothing) * old + self.smoothing * new
            self.model = NoiseModel(*(mix(o, n) for o, n in zip(
                dataclasses.astuple(self.model), dataclasses.astuple(fitted))))
        return self.model
