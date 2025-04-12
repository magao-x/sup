<template>
  <div class="viewport"
    @mousedown="dragStart"
    >
    <div
      class="pannable"
      :style="{ top: `${offsetY}px`, left: `${offsetX}px` }"
    >
      <managed-canvas
        :imageData="imageData"
        :width="width" :height="height" :scale="scale"
        @view-hover="$emit('view-hover', $event)"
      ></managed-canvas>
    </div>
  </div>
</template>

<style scoped>
.viewport {
  width: 100%;
  height: 100%;
  overflow: hidden;
  position: relative;
  background-color: #aaa;
}
.pannable {
  position: absolute;
  display: inline-flex;
  background: black;
}
</style>

<script lang="ts">
import Vue from "vue";
import ManagedCanvas from "./ManagedCanvas.vue";


export default Vue.extend({
  components: { ManagedCanvas },
  props: {
    width: Number,
    height: Number,
    scale: Number,
    imageData: ImageData,
    options: Object,
  },
  data: function () {
    return {
      dragging: false,
      offsetX: 0,
      offsetY: 0,
      lastX: null,
      lastY: null,
      // array: array,
    };
  },
  mounted() {
    this.reset();
  },
  watch: {
    options(newOptions) {
      if (newOptions.shouldReset) {
        this.reset();
      }
    },
  },
  methods: {
    reset() {
      this.dragEnd();
      let oW = this.$el.offsetWidth, oH = this.$el.offsetHeight;
      this.offsetX = oW / 2 - this.width / 2;
      this.offsetY = oH / 2 - this.height / 2;
      this.$emit("reset");
    },
    clampToBounds() {
      if (this.offsetX > this.$el.offsetWidth - 20) {
        this.offsetX = this.$el.offsetWidth - 20;
      } else if (this.offsetX < -(this.width - 20)) {
        this.offsetX = -(this.width - 20);
      }
      if (this.offsetY > this.$el.offsetHeight - 20) {
        this.offsetY = this.$el.offsetHeight - 20;
      } else if (this.offsetY < -(this.height - 20)) {
        this.offsetY = -(this.height - 20);
      }
    },
    dragMove(ev) {
      const diffX = ev.pageX - this.lastX;
      const diffY = ev.pageY - this.lastY;
      this.offsetX += diffX;
      this.offsetY += diffY;
      this.lastX = ev.pageX;
      this.lastY = ev.pageY;
      this.clampToBounds();
    },
    dragStart(ev) {
      this.dragging = true;
      this.lastX = ev.pageX;
      this.lastY = ev.pageY;
      this.moveHandler = document.addEventListener("mousemove", this.dragMove);
      this.releaseHandler = document.addEventListener("mouseup", this.dragEnd);
    },
    dragEnd() {
      this.dragging = false;
      this.lastX = null;
      this.lastY = null;
      document.removeEventListener("mousemove", this.dragMove);
      document.removeEventListener("mouseup", this.dragEnd);
    }
  },
});
</script>
