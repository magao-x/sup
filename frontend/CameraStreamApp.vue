<template>
  <view-arr id="view" 
    :array="array"
    :width="width"
    :height="height"
  ></view-arr>
</template>
<style lang="scss">
@import "./css/variables.scss";

body {
  margin: 0;
  padding: 0;
  min-width: 100vw;
  min-height: 100vh;
}
#view {
  width: 100%;
  height: 100vh;
}
</style>
<script>
import Vue from 'vue';
import indi from "~/mixins/indi.js";
import ViewArr from "~/components/viewarr/ViewArr.vue";


let buildConnectionString;
if (process.env.NODE_ENV == 'development') {
  buildConnectionString = function() {
    const apiPort = 8000;
    const wsProto = window.location.protocol == "https:" ? "wss:" : "ws:";
    let connectionString = wsProto + '//' + window.location.hostname;
    if (window.location.port) {
      connectionString += ':' + String(apiPort);
    }
    return connectionString;
  }
} else {
  buildConnectionString = function() {
    const wsProto = window.location.protocol == "https:" ? "wss:" : "ws:";
    let connectionString = wsProto + '//' + window.location.hostname;
    if (window.location.port) {
      connectionString += ':' + String(window.location.port);
    }
    return connectionString;
  }
}

const fTest20 = new Float32Array([
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
      1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
]);
const fTest20_2 = new Float32Array([0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
    0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0.,
    0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1.,
    1., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0.,
    1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
    1., 0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
    1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0.]);
const frames = [fTest20, fTest20_2];
const advanceMillis = 1000;

const refreshMillis = 2000;
let textEncoder = new TextEncoder();

import { Blosc, GZip, Zlib, LZ4, Zstd } from 'numcodecs';
// const codec = new Blosc();
const codec = Blosc.fromConfig({ clevel: 5, cname: 'lz4', shuffle: Blosc.SHUFFLE, blocksize: 0 });

export default Vue.extend({
  mixins: [indi],
  data() {
    return {
      array: fTest20_2,
      idx: 0,
      shmimName: null,
      videoSocket: null,
      videoReconnectionTimer: null,
      connected: false,
      refreshTimer: null,
      width: 0,
      height: 0,
    }
  },
  methods: {
    connectVideoSocket() {
      if (this.videoSocket !== null && (this.videoSocket.readyState == WebSocket.CONNECTING || this.videoSocket.readyState == WebSocket.OPEN)) {
        return this.videoSocket;
      }
      const connectionURL = buildConnectionString() + "/videosocket";
      console.log("Connecting to", connectionURL)
      let ws = new WebSocket(connectionURL);
      ws.addEventListener('open', this.onVideoSocketOpen);
      ws.addEventListener('message', this.onVideoSocketMessage);
      ws.addEventListener('close', this.onVideoSocketClose);
      ws.addEventListener('error', this.onVideoSocketError);
      this.videoSocket = ws;
      return ws;
    },
    onVideoSocketOpen(evt) {
      console.log(evt);
      this.connected = true;
    },
    async onVideoSocketMessage(evt) {
      console.log(evt);
      const bytesPerInt = 4;
      let shape = await evt.data.slice(0, 2 * bytesPerInt).arrayBuffer().then((buf) => new Uint32Array(buf));
      console.log("shape", shape);
      let buf = await evt.data.slice(2 * bytesPerInt).arrayBuffer();
      let arr = new Uint8Array(buf);
      console.log("arr", arr);
      const decoded = await codec.decode(arr);
      console.log("decoded", decoded);
      this.height = shape[0];
      this.width = shape[1];
      this.array = new Uint16Array(decoded.buffer);
    },
    onVideoSocketClose(evt) {
      console.log(evt);
      this.connected = false;
    },
    onVideoSocketError(evt) {
      console.log(evt);
      this.connected = false;
    },
    requestUpdate() {
      this.videoSocket.send(textEncoder.encode(this.shmimName));
    }
  },
  mounted() {
    // setInterval(() => {
    //   this.idx = (this.idx + 1) % frames.length;
    //   this.array = frames[this.idx];
    // }, advanceMillis);
    this.shmimName = window.location.hash.slice(1);
    this.connectVideoSocket();
    this.refreshTimer = setInterval(() => {return this.requestUpdate();}, refreshMillis);
    this.videoReconnectionTimer = setInterval(() => {
      if(this.videoSocket === null || this.videoSocket.readyState == WebSocket.CLOSED || this.videoSocket.readyState == WebSocket.CLOSING ) {
        this.connectVideoSocket();
      }
    }, 1000);
    console.log("Set reconnectionTimer id:", this.videoReconnectionTimer);
  },
  beforeUnmount() {
    if (this.videoReconnectionTimer) {
      clearInterval(this.videoReconnectionTimer);
    }
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  },
  components: {
    ViewArr,
  }
})
</script>