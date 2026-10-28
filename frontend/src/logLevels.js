// Severities a log message can open with, most severe first. Devices pad the
// shorter ones to four characters ("ERR  ..."). Matches LOG_LEVELS on the
// server, which keeps its history by the same levels.
export const LOG_LEVELS = ["EMER", "ALRT", "CRIT", "ERR", "WARN", "NOTE", "INFO"];

// The level a log message opens with, or null if it names none we know.
export function logLevel(log) {
  const level = log.message.slice(0, 4).trim();
  return LOG_LEVELS.includes(level) ? level : null;
}

// Keep only the newest `perLevel` messages at each level, and none that name
// no level, preserving arrival order. A flat cap would let a burst at one
// level push out every message at the others, so a viewer filtered down to
// errors could find none even though errors had come in.
export function trimPerLevel(logs, perLevel) {
  const kept = {};
  const result = [];
  for (let i = logs.length - 1; i >= 0; i--) {
    const level = logLevel(logs[i]);
    if (level === null || (kept[level] || 0) >= perLevel) {
      continue;
    }
    kept[level] = (kept[level] || 0) + 1;
    result.push(logs[i]);
  }
  return result.reverse();
}
