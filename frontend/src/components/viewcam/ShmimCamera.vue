<template>
  <div class="shmim-camera">
    <div :id="containerId" class="viewcam-container"></div>
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
.error {
  padding: $medgap $lggap;
  color: $danger-red;
}
</style>

<script>
import * as viewcam from "viewcam";
import DecodeWorker from "viewcam-codec/decode-worker.js?worker";
import { ViewcamFeed, quantizedThreshold, workerDecoder } from "viewcam-proto";
import utils from "@/utils.js";

// Frames allowed in flight on each feed. Six keeps 30 fps going over a
// 150 ms round trip; the dark changes so rarely that one is plenty.
// See "Choosing a window" in viewcam-proto/PROTOCOL.md.
const WINDOWS = { data: 6, dark: 1, saturation: 6 };
// Until turbo is switched on in viewcam's status bar, each feed gets at most
// this many frames a second. At one a second a window of one frame is
// plenty, and keeps a burst of frames from coming through ahead of the pacing.
const CAPPED_FPS = 1;
const CAPPED_WINDOW = 1;

let nextViewerId = 0;

// The feeds go to viewcam, which shows what they are doing in its status
// bar; this only connects them and reports what happens on them.
export default {
  props: {
    // The camera's shmim, and the shmims of its dark and saturation map, if it has them.
    name: { type: String, required: true },
    dark: { type: String, default: null },
    saturation: { type: String, default: null },
    // For a camera without a saturation map: data at or above this is saturated.
    saturationLevel: { type: Number, default: null },
  },
  data() {
    return {
      containerId: `viewcam-${nextViewerId++}`,
      error: null,
    };
  },
  async mounted() {
    // Not reactive: these are handles, not state to render.
    this.feeds = [
      { role: 'data', name: this.name },
      { role: 'dark', name: this.dark },
      { role: 'saturation', name: this.saturation },
    ].filter((feed) => feed.name);
    this.connections = [];
    this.turbo = false;
    this.worker = new DecodeWorker();
    this.decode = workerDecoder(this.worker);
    try {
      await viewcam.createViewer(this.containerId);
    } catch (e) {
      this.error = `Failed to start the camera viewer: ${e.message}`;
      return;
    }
    if (this.destroyed) return;
    if (!this.saturation && this.saturationLevel !== null) {
      viewcam.setSaturationLevel(this.containerId, this.saturationLevel);
      this.appliedSaturationLevel = this.saturationLevel;
    }
    for (const feed of this.feeds) viewcam.setFeed(this.containerId, feed.role, feed.name);
    viewcam.onStateChange(this.containerId, ({ turbo }) => {
      if (turbo !== this.turbo) this.setTurbo(turbo);
    });
    this.connections = this.feeds.map((feed) => this.connect(feed));
    document.addEventListener('visibilitychange', this.onVisibilityChange);
  },
  beforeUnmount() {
    this.destroyed = true;
    document.removeEventListener('visibilitychange', this.onVisibilityChange);
    for (const connection of this.connections) connection.close();
    this.worker.terminate();
    if (viewcam.hasViewer(this.containerId)) viewcam.destroyViewer(this.containerId);
  },
  methods: {
    connect(feed) {
      const id = this.containerId;
      const show = {
        data: (frame) => {
          this.followSaturationLevel(frame.quantization);
          viewcam.setData(id, frame.pixels, frame.width, frame.height, frame.dtype);
        },
        dark: (frame) => viewcam.setDark(id, frame.pixels, frame.width, frame.height, frame.dtype),
        saturation: (frame) => viewcam.setSaturation(id, frame.pixels, frame.width, frame.height, frame.dtype),
      }[feed.role];
      const clear = {
        data: () => {},
        dark: () => viewcam.clearDark(id),
        saturation: () => viewcam.clearSaturation(id),
      }[feed.role];
      return new ViewcamFeed(utils.buildWebSocketUrl(`ws/viewcam/${encodeURIComponent(feed.name)}`), {
        decode: this.decode,
        onReceive: (bytes) => viewcam.noteReceived(id, bytes),
        windowFrames: this.windowFor(feed),
        maxFps: this.turbo ? 0 : CAPPED_FPS,
        onStatus: (status) => viewcam.setFeedConnection(id, feed.role, status),
        onFrame: (frame) => {
          show(frame);
          viewcam.noteFeedFrame(id, feed.role, frame.seq, frame.width, frame.height, frame.dtype);
        },
        onEmpty: () => {
          clear();
          viewcam.noteFeedEmpty(id, feed.role);
        },
      });
    },
    // A quantized frame's values are rounded, so a saturated pixel can come
    // back a little under the saturation level: compare with the threshold
    // between the level's code and the one below it instead.
    followSaturationLevel(quantization) {
      if (this.saturation || this.saturationLevel === null) return;
      const level = quantization ? quantizedThreshold(this.saturationLevel, quantization) : this.saturationLevel;
      if (level === this.appliedSaturationLevel) return;
      this.appliedSaturationLevel = level;
      viewcam.setSaturationLevel(this.containerId, level);
    },
    windowFor(feed) {
      if (document.hidden) return 0;
      return this.turbo ? WINDOWS[feed.role] : CAPPED_WINDOW;
    },
    setTurbo(turbo) {
      this.turbo = turbo;
      this.feeds.forEach((feed, i) => {
        const connection = this.connections[i];
        if (!connection) return;
        connection.setMaxFps(turbo ? 0 : CAPPED_FPS);
        connection.setWindow(this.windowFor(feed));
      });
    },
    onVisibilityChange() {
      // A hidden tab pauses its feeds rather than closing them; showing it
      // again brings the newest frames straight away.
      this.feeds.forEach((feed, i) => {
        this.connections[i].setWindow(this.windowFor(feed));
      });
    },
  },
};
</script>
