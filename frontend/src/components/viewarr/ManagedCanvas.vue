<template>
  <div>
    <canvas
      ref="managedCanvas"
      :width="width"
      :height="height"
      :style="{
        width: `${scale * width}px`,
        height: `${scale * height}px`,
      }"
      @mousemove="hover"
      @mouseleave="$emit('view-hover', {x: null, y: null, value: null})"
    ></canvas>
  </div>
</template>
<style scoped>
div {
  display: inline-flex;
}
canvas {
  image-rendering: pixelated;
}
</style>
<script lang="ts">
import Vue from "vue";

// const WIDTH = 200;
// const HEIGHT = 200;

export default Vue.extend({
  // props: ['imageData'],
  props: ['array', 'width', 'height', 'scale', 'imageData'],
  data: function () {
    // const arrayBuffer = new ArrayBuffer(WIDTH * HEIGHT * 4);
    // const pixels = new Uint8ClampedArray(arrayBuffer);
    // const imageData = new ImageData(this.width, this.height);
    // const pixels = imageData.data;
    // for (let y = 0; y < this.height; y++) {
    //   for (let x = 0; x < this.width; x++) {
    //     const i = (y * this.width + x) * 4;
    //     pixels[i] = x; // red
    //     pixels[i + 1] = y; // green
    //     pixels[i + 2] = 0; // blue
    //     pixels[i + 3] = 255; // alpha
    //   }
    // }

    return {
      // array: imageData,
      // dataWidth: this.width,
      // dataHeight: this.height,
      // scale: 1.0,
    };
  },
  computed: {
    // imageData() {
    //   const theImageData = new ImageData(this.width, this.height);
    //   const pixels = theImageData.data;
    //   for (let y = 0; y < this.height; y++) {
    //     for (let x = 0; x < this.width; x++) {
    //       const srcIdx = y * this.width + x;
    //       const destIdx = ((this.height - y - 1) * this.width + x) * 4;
    //       const intensity = this.array[srcIdx] > 256 ? 255 : 0;
    //       // pixels[destIdx] = intensity; // red
    //       // pixels[destIdx + 1] = 0; // green
    //       // pixels[destIdx + 2] = 0; // blue
    //       // pixels[destIdx + 3] = 255; // alpha
    //     }
    //   }
    //   return theImageData;
    // },
  },
  methods: {
    hover(ev) {
      // read pixel coordinates from canvas
      const canvas = this.$refs.managedCanvas;
      const rect = canvas.getBoundingClientRect();
      const rawX = (ev.clientX - rect.left) / this.scale;
      const rawY = (ev.clientY - rect.top) / this.scale;
      
      // read value from input buffer
      this.$emit("view-hover", {x: rawX, y: rawY, value: null});
      ev;
      canvas;
    },
    render() {
      this.$refs.managedCanvas.width = this.width;
      this.$refs.managedCanvas.height = this.height;
      const ctx = this.$refs.managedCanvas.getContext("2d");
      ctx.putImageData(this.imageData, 0, 0);
      console.log('redered', this.imageData);
    },
  },
  mounted() {
    this.render();
  },
  watch: {
    imageData() {
      this.render();
    },
  },
});
</script>
