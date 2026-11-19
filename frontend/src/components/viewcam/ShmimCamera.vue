<template>
  <div class="shmim-camera">
    <div :id="containerId" class="viewcam-container"></div>
    <div class="feed-status">
      <span v-for="feed in shownFeeds" :key="feed.role" class="feed" :class="feed.status">
        <span class="feed-name">{{ feed.name }}</span>
        <span v-if="feed.status !== 'open'">{{ feed.status }}</span>
        <span v-else-if="feed.empty">no image</span>
        <span v-else-if="feed.width">
          {{ feed.width }}×{{ feed.height }} {{ feed.dtype }} · #{{ feed.seq }}
          <template v-if="feed.role !== 'dark'"> · {{ feed.fps.toFixed(1) }} fps</template>
        </span>
        <span v-else>waiting</span>
      </span>
      <span class="feed bandwidth" title="Received over the last few seconds, all feeds together">
        <span class="feed-name">total</span>{{ formatRate(bandwidth) }}
      </span>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.shmim-camera {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}
.viewcam-container {
  flex: 1;
  min-height: 0;
}
.feed-status {
  display: flex;
  flex-wrap: wrap;
  gap: 0 1.5em;
  padding: $medgap $lggap;
  font-family: monospace;
  font-size: 0.85em;
  color: var(--fg-inactive);
  background: var(--inset-bg);
}
.feed-name {
  color: $plasma-blue;
  margin-right: 0.5em;
}
.feed.closed, .feed.connecting {
  color: $beware-orange;
}
.bandwidth {
  margin-left: auto;
}
.error {
  padding: $medgap $lggap;
  color: $danger-red;
}
</style>

<script>
import * as viewcam from "viewcam";
import DecodeWorker from "viewcam-codec/decode-worker.js?worker";
import { ViewcamFeed, workerDecoder } from "viewcam-proto";
import utils from "@/utils.js";

// Frames allowed in flight on each feed. Six keeps 30 fps going over a
// 150 ms round trip; the dark changes so rarely that one is plenty.
// See "Choosing a window" in viewcam-proto/PROTOCOL.md.
const WINDOWS = { data: 6, dark: 1, saturation: 6 };
// Over how many frames the frame rate is averaged.
const FPS_FRAMES = 10;
// Over how long the bandwidth is averaged, and how often it is updated.
const BANDWIDTH_WINDOW_MS = 5000;
const BANDWIDTH_UPDATE_MS = 1000;

let nextViewerId = 0;

export default {
  props: {
    // The camera's shmim, and the shmims of its dark and saturation map, if it has them.
    name: { type: String, required: true },
    dark: { type: String, default: null },
    saturation: { type: String, default: null },
  },
  data() {
    return {
      containerId: `viewcam-${nextViewerId++}`,
      feeds: [
        { role: 'data', name: this.name },
        { role: 'dark', name: this.dark },
        { role: 'saturation', name: this.saturation },
      ].filter((feed) => feed.name).map((feed) => ({
        ...feed, status: 'connecting', empty: false, seq: null, width: 0, height: 0, dtype: '', fps: 0,
      })),
      error: null,
      bandwidth: 0,
    };
  },
  computed: {
    // A dark or saturation shmim is optional: many cameras have neither, so
    // those feeds are listed only while they have an image. The data feed
    // is always listed, as the one that says whether the camera is there.
    shownFeeds() {
      return this.feeds.filter((feed) => feed.role === 'data' || (feed.width && !feed.empty));
    },
  },
  async mounted() {
    // Not reactive: these are handles, not state to render.
    this.connections = [];
    // [time, bytes] of each message received on any feed, oldest first.
    this.received = [];
    this.openedAt = performance.now();
    this.bandwidthTimer = setInterval(this.updateBandwidth, BANDWIDTH_UPDATE_MS);
    this.worker = new DecodeWorker();
    this.decode = workerDecoder(this.worker);
    try {
      await viewcam.createViewer(this.containerId);
    } catch (e) {
      this.error = `Failed to start the camera viewer: ${e.message}`;
      return;
    }
    if (this.destroyed) return;
    this.connections = this.feeds.map((feed) => this.connect(feed));
    document.addEventListener('visibilitychange', this.onVisibilityChange);
  },
  beforeUnmount() {
    this.destroyed = true;
    document.removeEventListener('visibilitychange', this.onVisibilityChange);
    clearInterval(this.bandwidthTimer);
    for (const connection of this.connections) connection.close();
    this.worker.terminate();
    if (viewcam.hasViewer(this.containerId)) viewcam.destroyViewer(this.containerId);
  },
  methods: {
    connect(feed) {
      const show = {
        data: (frame) => viewcam.setData(this.containerId, frame.pixels, frame.width, frame.height, frame.dtype),
        dark: (frame) => viewcam.setDark(this.containerId, frame.pixels, frame.width, frame.height, frame.dtype),
        saturation: (frame) => viewcam.setSaturation(this.containerId, frame.pixels, frame.width, frame.height, frame.dtype),
      }[feed.role];
      const clear = {
        data: () => {},
        dark: () => viewcam.clearDark(this.containerId),
        saturation: () => viewcam.clearSaturation(this.containerId),
      }[feed.role];
      const arrivals = [];
      return new ViewcamFeed(utils.buildWebSocketUrl(`ws/viewcam/${encodeURIComponent(feed.name)}`), {
        decode: this.decode,
        onReceive: (bytes) => this.received.push([performance.now(), bytes]),
        windowFrames: document.hidden ? 0 : WINDOWS[feed.role],
        onStatus: (status) => {
          feed.status = status;
          arrivals.length = 0;
          feed.fps = 0;
        },
        onFrame: (frame) => {
          show(frame);
          Object.assign(feed, {
            empty: false, seq: frame.seq.toString(), width: frame.width, height: frame.height, dtype: frame.dtype,
          });
          arrivals.push(performance.now());
          if (arrivals.length > FPS_FRAMES) arrivals.shift();
          if (arrivals.length > 1) {
            feed.fps = 1000 * (arrivals.length - 1) / (arrivals.at(-1) - arrivals[0]);
          }
        },
        onEmpty: () => {
          clear();
          Object.assign(feed, { empty: true, width: 0, height: 0 });
        },
      });
    },
    updateBandwidth() {
      const now = performance.now();
      const since = now - BANDWIDTH_WINDOW_MS;
      while (this.received.length && this.received[0][0] < since) this.received.shift();
      // Averaged over the whole window, or since the view opened if sooner,
      // so a quiet spell counts as quiet rather than being skipped over.
      const span = Math.min(BANDWIDTH_WINDOW_MS, now - this.openedAt);
      const bytes = this.received.reduce((total, [, n]) => total + n, 0);
      this.bandwidth = span > 0 ? 1000 * bytes / span : 0;
    },
    formatRate(bytesPerSec) {
      const bits = 8 * bytesPerSec;
      if (bits >= 1e6) return `${(bits / 1e6).toFixed(1)} Mbit/s`;
      if (bits >= 1e3) return `${(bits / 1e3).toFixed(1)} kbit/s`;
      return `${bits.toFixed(0)} bit/s`;
    },
    onVisibilityChange() {
      // A hidden tab pauses its feeds rather than closing them; showing it
      // again brings the newest frames straight away.
      this.feeds.forEach((feed, i) => {
        this.connections[i].setWindow(document.hidden ? 0 : WINDOWS[feed.role]);
      });
    },
  },
};
</script>
