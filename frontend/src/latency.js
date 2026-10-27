// Measuring how long server updates take to reach this browser.
//
// The server stamps every batch with its own clock, which cannot be compared
// to ours directly --- the offset between the two is unknown and includes
// whatever clock skew exists between Chile and wherever the browser is. What
// *is* comparable is that difference over time: whatever the offset is, it is
// constant, so the smallest difference we have ever seen is our baseline of
// "arrived as fast as this connection goes", and anything above it is delay
// that accumulated on the way here.
const MAX_SAMPLES = 200;

let baselineOffsetMs = null;
let lastBatch = null;
const recentSlowBatches = [];

/**
 * Record the arrival of a server batch.
 *
 * Returns a description of how late it was relative to the best transit this
 * session has seen, which is the useful number: a steadily growing lateness
 * means updates are queueing somewhere between the server and here.
 */
export function noteBatchArrival(sentAtIso, byteLength) {
  const receivedAtMs = Date.now();
  const sentAtMs = Date.parse(sentAtIso);
  const batch = { receivedAtMs, byteLength, latenessMs: null };
  if (!Number.isNaN(sentAtMs)) {
    const offsetMs = receivedAtMs - sentAtMs;
    if (baselineOffsetMs === null || offsetMs < baselineOffsetMs) {
      baselineOffsetMs = offsetMs;
    }
    batch.latenessMs = offsetMs - baselineOffsetMs;
  }
  lastBatch = batch;
  if (batch.latenessMs !== null && batch.latenessMs > 1000) {
    recentSlowBatches.push(batch);
    if (recentSlowBatches.length > MAX_SAMPLES) {
      recentSlowBatches.shift();
    }
    console.warn(
      `[sup] server update arrived ${(batch.latenessMs / 1000).toFixed(1)}s later than this ` +
      `connection's best (${(byteLength / 1024).toFixed(0)} kB). Anything waiting on it ` +
      `--- including audible alerts --- is late by at least that much.`
    );
  }
  return batch;
}

/** The most recently arrived batch, for attributing a delay to its delivery. */
export function lastBatchArrival() {
  return lastBatch;
}

export function transitSummary() {
  return {
    baselineOffsetMs,
    lastLatenessMs: lastBatch ? lastBatch.latenessMs : null,
    slowBatchCount: recentSlowBatches.length,
    worstLatenessMs: recentSlowBatches.reduce((worst, b) => Math.max(worst, b.latenessMs), 0),
  };
}

/**
 * What the browser's Resource Timing says about fetching a URL: whether it
 * came off the network or out of the cache, and how long it took.
 *
 * This is what separates "the clip had to cross an ocean" from every other
 * reason an alert might be late.
 */
export function describeFetch(url, sincePerfMs) {
  if (typeof performance === 'undefined' || !performance.getEntriesByName) {
    return null;
  }
  // Only entries from *this* load count. A play served out of the cache may
  // record no entry at all, and the stale entry left by an earlier network
  // fetch of the same URL would otherwise be read as a fresh download ---
  // reporting the opposite of the truth for the question this exists to
  // answer.
  const entries = performance.getEntriesByName(url)
    .filter((entry) => sincePerfMs === undefined || entry.startTime >= sincePerfMs);
  if (entries.length === 0) {
    return null;
  }
  const entry = entries[entries.length - 1];
  // A body that was decoded but not transferred came from the cache. Browsers
  // also report 0 for both when timing information is withheld, so a zero
  // decoded size means "cannot tell" rather than "cached".
  const cached = entry.transferSize === 0 && entry.decodedBodySize > 0;
  return {
    cached,
    durationMs: Math.round(entry.duration),
    transferredBytes: entry.transferSize,
    bodyBytes: entry.decodedBodySize,
  };
}

export default { noteBatchArrival, lastBatchArrival, transitSummary, describeFetch };
