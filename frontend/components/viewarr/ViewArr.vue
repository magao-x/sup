<template>
  <div class="viewarr" @keypress="keyup" tabindex="0">
    <div class="toolbar">
      <div class="coords">
        <input disabled :value="hoverX">
        <input disabled :value="hoverY">
        <input disabled :value="hoverValue">
      </div>
      <div class="limits-picker"><select><option>min/max</option></select></div>
      <div class="limits">
        <input value="min">
        <span>-</span>
        <input value="max">
      </div>
      <div class="stretch"><input type="checkbox">log</div>
      <button @click="requestReset">reset</button>
    </div>
    <slippy-view
      :width="width"
      :height="height"
      :scale="scale"
      :imageData="imageData"
      :options="{shouldReset: shouldViewReset}"
      @reset="onReset"
      @view-hover="updateHover"
      style="flex: 1"
    ></slippy-view>
  </div>
</template>

<style scoped>
.viewarr {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.toolbar {
  background-color: #aaa;
  display: flex;
}
.coords, .limits {
  flex:1 ;
  display: flex;
}
.coords > *, .limits > * {
  flex: 1;
  width: 0;
  max-width: 5em;
}
</style>

<script lang="ts">
import Vue from 'vue'
import SlippyView from './SlippyView.vue';


export default Vue.extend({
  components: { SlippyView },
  props: ["array", "width", "height"],
  data() {
    return {
      shouldViewReset: false,
      // array: frames[0],
      scale: 1,
      idx: 0,
      // width: 20,
      // height: 20,
      hoverX: null,
      hoverY: null,
      hoverValue: null,
    };
  },
  computed: {
    imageData() {
      const theImageData = new ImageData(this.width, this.height);
      const pixels = theImageData.data;
      console.log("imagedata");
      let fired = false;
      for (let y = 0; y < this.height; y++) {
        for (let x = 0; x < this.width; x++) {
          const srcIdx = y * this.width + x;
          const destIdx = ((this.height - y - 1) * this.width + x) * 4;
          // const intensity = this.array[srcIdx] / ;
          if (!fired) {
            fired = true;
            console.log('foo', this.array[srcIdx], this.array[srcIdx] >> 2);
          }
          const rescaled = this.array[srcIdx] >> 2;
          pixels[destIdx] = rescaled; // red
          pixels[destIdx + 1] = rescaled; // green
          pixels[destIdx + 2] = rescaled; // blue
          pixels[destIdx + 3] = 255; // alpha
        }
      }
      return theImageData;
    }
  },
  methods: {
    requestReset() {
      this.shouldViewReset = true;
    },
    onReset() {
      this.shouldViewReset = false;
    },
    updateHover(payload) {
      this.hoverX = payload.x;
      this.hoverY = payload.y;
      this.hoverValue = payload.value;
    },
    keyup(evt) {
      console.log(evt);
      if (/\d/.test(evt.key)) {
        const factor = Number(evt.key);
        if (factor > 0) {
          this.scale = factor;
        }
      }
    }
  }
})
</script>
