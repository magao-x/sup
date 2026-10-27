// Browser-side playback for the audibleAlerts subsystem.
//
// The audibleAlerts device (INDI name maggieo_x) announces every clip it plays
// by updating its `playback` property, which already reaches this browser over
// the regular INDI websocket. All this module adds is the audio: it watches
// that property for a newer timestamp and fetches the clip the device named,
// mirroring what audibleAlertsClient does natively on control room machines.
//
// Playback is opt-in and off by default, and the player never writes INDI --- a
// web listener cannot unmute the instrument for everyone else. The device's own
// mute switch still gates everything, because a muted device publishes no
// playback updates at all.
import store from '@/store.js';
import utils from '@/utils.js';
import latency from '@/latency.js';

// Queued clips are dropped once they have waited this long. Alerts are about
// what the instrument is doing *now*; a laptop coming back from sleep should
// stay quiet rather than recite the backlog.
const MAX_QUEUE_AGE_SEC = 20;
// Cap on how far behind the player may fall before it starts dropping the
// oldest queued clips.
const MAX_QUEUE_LENGTH = 5;

// One element, created inside the click that enables alerts and reused
// forever: browsers grant autoplay permission to the element that existed
// during the gesture, and iOS Safari in particular will not extend it to one
// created later.
let audioElement = null;
let queue = [];
let playing = false;
// Server-clock timestamps, used only to order and de-duplicate updates against
// each other, never against the browser clock.
let lastSeenPlaybackMs = null;
let objectUrls = {};
// Set once a play() has actually resolved. Until then the element may be one
// the browser will refuse to play, and the gesture handlers rebuild it.
let unlocked = false;
// The alert currently on the audio element, and a short history of the ones
// before it. Observers report latency that is hard to reproduce --- Chile to
// Europe is a long way --- so every alert accounts for where its time went.
let currentPlayback = null;
const playbackHistory = [];
const MAX_HISTORY = 50;
// Clips this page has played before. A cached play can leave no Resource
// Timing entry behind, so knowing we have played it already is what separates
// "came out of the cache" from "cannot tell".
const previouslyPlayed = new Set();

function clipUrl(file) {
  const encoded = file.split('/').map(encodeURIComponent).join('/');
  return utils.buildBackendUrl(`audible-alerts/clip/${encoded}`);
}

function elementValue(property, name) {
  const element = property._elements ? property._elements[name] : null;
  return element ? element._value : null;
}

/**
 * Build a short confirmation tone as a WAV blob.
 *
 * Generated rather than bundled so enabling alerts can make a sound
 * immediately, without a round trip, while the enabling click still counts as
 * the gesture that unlocks playback. It doubles as a way to check that the
 * right output device is selected before relying on alerts.
 */
function toneUrl(key, { durationSec, freqHz, amplitude }) {
  if (objectUrls[key] !== undefined) {
    return objectUrls[key];
  }
  const sampleRate = 22050;
  const frames = Math.floor(durationSec * sampleRate);
  const buffer = new ArrayBuffer(44 + frames * 2);
  const view = new DataView(buffer);
  const writeAscii = (offset, text) => {
    for (let i = 0; i < text.length; i++) {
      view.setUint8(offset + i, text.charCodeAt(i));
    }
  };
  writeAscii(0, 'RIFF');
  view.setUint32(4, 36 + frames * 2, true);
  writeAscii(8, 'WAVE');
  writeAscii(12, 'fmt ');
  view.setUint32(16, 16, true);     // PCM header length
  view.setUint16(20, 1, true);      // PCM, uncompressed
  view.setUint16(22, 1, true);      // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);  // bytes per second
  view.setUint16(32, 2, true);      // bytes per frame
  view.setUint16(34, 16, true);     // bits per sample
  writeAscii(36, 'data');
  view.setUint32(40, frames * 2, true);
  for (let i = 0; i < frames; i++) {
    const t = i / sampleRate;
    // Taper both ends, or the discontinuity reads as a click.
    const envelope = Math.min(1, t / 0.01, (durationSec - t) / 0.03);
    const sample = Math.sin(2 * Math.PI * freqHz * t) * envelope * amplitude;
    view.setInt16(44 + i * 2, sample * 0x7fff, true);
  }
  objectUrls[key] = URL.createObjectURL(new Blob([buffer], { type: 'audio/wav' }));
  return objectUrls[key];
}

function chimeUrl() {
  return toneUrl('chime', { durationSec: 0.18, freqHz: 660, amplitude: 0.25 });
}

// Digital silence, for asking the browser whether it would allow playback
// without anybody hearing the question. Deliberately not a muted element: the
// autoplay policy treats muted playback as always permitted, so a muted probe
// would answer yes even where audible playback is refused.
function silenceUrl() {
  return toneUrl('silence', { durationSec: 0.05, freqHz: 440, amplitude: 0 });
}

function ensureAudioElement({ rebuild = false } = {}) {
  if (audioElement !== null && rebuild && !unlocked) {
    // iOS Safari grants playback to the element that existed during the
    // gesture and will not extend it to one built earlier, so an element that
    // has never successfully played gets replaced rather than retried.
    audioElement.removeEventListener('playing', onClipStarted);
    audioElement.removeEventListener('ended', onClipFinished);
    audioElement.removeEventListener('error', onClipFinished);
    audioElement.pause();
    audioElement = null;
  }
  if (audioElement === null) {
    audioElement = new Audio();
    audioElement.addEventListener('playing', onClipStarted);
    audioElement.addEventListener('ended', onClipFinished);
    audioElement.addEventListener('error', onClipFinished);
  }
  return audioElement;
}

function describeClipSource(record) {
  const fetched = latency.describeFetch(record.url, record.requestedAtPerfMs);
  if (fetched === null) {
    // No fetch happened for this play. If the clip has played before, the
    // audio came out of the cache; otherwise the browser is simply not telling
    // us, and guessing would defeat the purpose.
    return record.playedBefore
      ? { text: 'clip from browser cache (no fetch)', detail: { cached: true } }
      : { text: 'clip source unknown', detail: null };
  }
  if (fetched.cached) {
    return { text: 'clip from browser cache', detail: fetched };
  }
  return {
    text: `clip fetched in ${(fetched.durationMs / 1000).toFixed(2)}s `
      + `(${Math.round(fetched.transferredBytes / 1024)} kB over the network)`,
    detail: fetched,
  };
}

/**
 * Report where an alert's delay went, once it is actually making sound.
 *
 * The four places time can go are each measured separately, because they call
 * for different fixes: getting the update here, waiting behind another clip,
 * fetching the audio, and the browser starting playback.
 */
function reportPlayback(record) {
  record.startedAtMs = Date.now();
  record.sinceArrivalMs = record.startedAtMs - record.receivedAtMs;
  const source = describeClipSource(record);
  record.clipSource = source.detail;

  const parts = [
    record.file,
    `announced ${record.announcedAtIso}`,
    record.batchLatenessMs === null
      ? 'delivery delay unknown'
      : `delivery +${(record.batchLatenessMs / 1000).toFixed(2)}s over this connection's best`,
    `queued ${(record.queuedMs / 1000).toFixed(2)}s`,
    source.text,
    `playing ${(record.sinceArrivalMs / 1000).toFixed(2)}s after the update arrived`,
  ];
  console.log(`[audible-alerts] ${parts.join(' | ')}`, record);

  playbackHistory.push(record);
  if (playbackHistory.length > MAX_HISTORY) {
    playbackHistory.shift();
  }
}

function onClipStarted() {
  if (currentPlayback !== null && currentPlayback.startedAtMs === null) {
    reportPlayback(currentPlayback);
  }
}

function onClipFinished() {
  playing = false;
  currentPlayback = null;
  playNext();
}

function onPlaybackRejected(err) {
  playing = false;
  if (err && err.name === 'NotAllowedError') {
    // The browser is withholding autoplay permission, so there is no point
    // piling up clips it will not play. Surfacing this lets the control offer
    // the click that fixes it.
    queue = [];
    store.commit('setAudibleAlertsBlocked', true);
    console.warn('Audible alerts blocked by the browser until audio is allowed', err);
    return;
  }
  console.warn('Could not play audible alert', err);
  playNext();
}

function start(url, options = {}) {
  const element = ensureAudioElement(options);
  playing = true;
  element.volume = store.state.audibleAlerts.volume;
  element.src = url;
  const started = element.play();
  // Older browsers return undefined instead of a promise.
  if (started !== undefined) {
    return started.then(() => {
      unlocked = true;
      store.commit('setAudibleAlertsBlocked', false);
    }).catch(onPlaybackRejected);
  }
  unlocked = true;
  return Promise.resolve();
}

function playNext() {
  if (playing || audioElement === null) {
    return;
  }
  while (queue.length > 0) {
    const next = queue.shift();
    if (Date.now() - next.receivedAtMs > MAX_QUEUE_AGE_SEC * 1000) {
      console.warn(
        `[audible-alerts] dropped ${next.file}: it waited `
        + `${((Date.now() - next.receivedAtMs) / 1000).toFixed(1)}s, longer than an alert stays useful`
      );
      continue;
    }
    next.queuedMs = Date.now() - next.receivedAtMs;
    next.playedBefore = previouslyPlayed.has(next.url);
    next.requestedAtPerfMs = performance.now();
    previouslyPlayed.add(next.url);
    currentPlayback = next;
    start(next.url);
    return;
  }
}

/**
 * Note a `playback` property update and play the clip it names, if the user
 * has opted in. Safe (and expected) to call on every update of the property.
 */
export function observePlayback(property) {
  if (!property) {
    return;
  }
  const timestampMs = Date.parse(property.timestamp);
  if (Number.isNaN(timestampMs)) {
    return;
  }
  // INDI re-sends the property on every (re)connection and the device leaves
  // the last utterance sitting in it, so the first value this page sees is
  // history, not news. Note where the stream stands and stay quiet; otherwise
  // a reload would repeat something the control room already heard.
  if (lastSeenPlaybackMs === null) {
    lastSeenPlaybackMs = timestampMs;
    return;
  }
  if (timestampMs <= lastSeenPlaybackMs) {
    return;
  }
  // Advance before the opt-in check, so that enabling alerts never replays
  // whatever happened while they were off.
  lastSeenPlaybackMs = timestampMs;
  if (!store.state.audibleAlerts.enabled || store.state.audibleAlerts.blocked) {
    return;
  }
  const file = elementValue(property, 'file');
  if (!file) {
    return;
  }
  const batch = latency.lastBatchArrival();
  queue.push({
    file,
    url: clipUrl(file),
    speech: elementValue(property, 'speech'),
    announcedAtIso: property.timestamp,
    // Our own clock, so staleness never depends on agreement between this
    // browser and the host running the device.
    receivedAtMs: Date.now(),
    // How late the batch carrying this alert was, relative to the fastest
    // delivery this connection has managed.
    batchLatenessMs: batch ? batch.latenessMs : null,
    batchBytes: batch ? batch.byteLength : null,
    queuedMs: null,
    startedAtMs: null,
  });
  if (queue.length > MAX_QUEUE_LENGTH) {
    queue.splice(0, queue.length - MAX_QUEUE_LENGTH);
  }
  playNext();
}

/**
 * Turn on playback. Must be called directly from a user gesture: that is what
 * earns the browser's permission to play audio for the rest of the session.
 */
export function enable() {
  store.commit('setAudibleAlertsBlocked', false);
  store.commit('setAudibleAlertsEnabled', true);
  playChime();
}

export function disable() {
  queue = [];
  playing = false;
  if (audioElement !== null) {
    audioElement.pause();
  }
  store.commit('setAudibleAlertsEnabled', false);
}

/**
 * Play the confirmation tone, to check the output device. Call from a user
 * gesture: it doubles as the way to recover from a browser that is refusing
 * playback, which only a gesture (or a site permission) can lift.
 */
export function playChime() {
  store.commit('setAudibleAlertsBlocked', false);
  return start(chimeUrl(), { rebuild: true });
}

/**
 * Re-arm playback on page load for someone who had alerts on last time.
 *
 * Autoplay permission is not ours to ask for: it is a site permission the user
 * grants in browser settings (Chrome calls it Sound, Firefox Autoplay, Safari
 * Auto-Play), and Chrome additionally grants it on its own to sites where the
 * user plays audio often. Where it has been granted, alerts should simply
 * resume across reloads without anybody clicking anything. Where it has not,
 * we find out here --- quietly, before an alert is riding on the answer ---
 * and the control shows that it needs a click.
 */
export function restoreSession() {
  if (!store.state.audibleAlerts.enabled) {
    return Promise.resolve(false);
  }
  // Browsers that implement it will just tell us.
  if (typeof navigator !== 'undefined' && typeof navigator.getAutoplayPolicy === 'function') {
    try {
      const policy = navigator.getAutoplayPolicy('mediaelement');
      if (policy !== 'allowed') {
        store.commit('setAudibleAlertsBlocked', true);
        return Promise.resolve(false);
      }
      ensureAudioElement();
      unlocked = true;
      return Promise.resolve(true);
    } catch (err) {
      console.debug('getAutoplayPolicy unavailable for mediaelement', err);
    }
  }
  // Otherwise ask the only way there is: try to play something inaudible.
  return start(silenceUrl()).then(() => {
    playing = false;
    if (audioElement !== null) {
      audioElement.pause();
    }
    return !store.state.audibleAlerts.blocked;
  });
}

export function setVolume(volume) {
  store.commit('setAudibleAlertsVolume', volume);
  if (audioElement !== null) {
    audioElement.volume = store.state.audibleAlerts.volume;
  }
}

/**
 * What the player has been doing, for an observer to copy out of the console.
 *
 * Exposed on `window` so that diagnosing a latency report needs no more
 * instruction than "open the console and run supAudibleAlerts.report()".
 */
export function report() {
  return {
    enabled: store.state.audibleAlerts.enabled,
    blocked: store.state.audibleAlerts.blocked,
    queueDepth: queue.length,
    delivery: latency.transitSummary(),
    playbacks: playbackHistory.map((record) => ({
      file: record.file,
      announced: record.announcedAtIso,
      deliveryLatenessMs: record.batchLatenessMs,
      batchBytes: record.batchBytes,
      queuedMs: record.queuedMs,
      msFromArrivalToSound: record.sinceArrivalMs,
      clip: record.clipSource,
    })),
  };
}

if (typeof window !== 'undefined') {
  window.supAudibleAlerts = {
    report,
    // Pre-formatted, because the usual request is "paste what it says".
    text: () => JSON.stringify(report(), null, 2),
  };
}

export default {
  observePlayback, enable, disable, playChime, setVolume, restoreSession, report,
};
