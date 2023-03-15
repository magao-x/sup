
import Vue from 'vue';
import common from "./common.js";
import video from "./video.js";
import CameraStreamApp from "./CameraStreamApp.vue";

new Vue({
  mixins: [common],
  render: h => h(CameraStreamApp),
}).$mount('#app')

