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
let chimeObjectUrl = null;

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
function chimeUrl() {
  if (chimeObjectUrl !== null) {
    return chimeObjectUrl;
  }
  const sampleRate = 22050, durationSec = 0.18, freqHz = 660;
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
    const sample = Math.sin(2 * Math.PI * freqHz * t) * envelope * 0.25;
    view.setInt16(44 + i * 2, sample * 0x7fff, true);
  }
  chimeObjectUrl = URL.createObjectURL(new Blob([buffer], { type: 'audio/wav' }));
  return chimeObjectUrl;
}

function ensureAudioElement() {
  if (audioElement === null) {
    audioElement = new Audio();
    audioElement.addEventListener('ended', onClipFinished);
    audioElement.addEventListener('error', onClipFinished);
  }
  return audioElement;
}

function onClipFinished() {
  playing = false;
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

function start(url) {
  const element = ensureAudioElement();
  playing = true;
  element.volume = store.state.audibleAlerts.volume;
  element.src = url;
  const started = element.play();
  // Older browsers return undefined instead of a promise.
  if (started !== undefined) {
    started.catch(onPlaybackRejected);
  }
}

function playNext() {
  if (playing || audioElement === null) {
    return;
  }
  while (queue.length > 0) {
    const next = queue.shift();
    if (Date.now() - next.receivedAtMs > MAX_QUEUE_AGE_SEC * 1000) {
      console.debug('Dropping stale audible alert', next.file);
      continue;
    }
    start(clipUrl(next.file));
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
  queue.push({
    file,
    speech: elementValue(property, 'speech'),
    // Our own clock, so staleness never depends on agreement between this
    // browser and the host running the device.
    receivedAtMs: Date.now(),
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
  ensureAudioElement();
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

/** Play the confirmation tone, to check the output device. */
export function playChime() {
  store.commit('setAudibleAlertsBlocked', false);
  start(chimeUrl());
}

export function setVolume(volume) {
  store.commit('setAudibleAlertsVolume', volume);
  if (audioElement !== null) {
    audioElement.volume = store.state.audibleAlerts.volume;
  }
}

export default { observePlayback, enable, disable, playChime, setVolume };
