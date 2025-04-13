<template>
  <div class="legend">
    <div
      class="line-legend"
      v-for="(lineData, key, idx) in data"
      :key="key"
      :style="{color: dataColors[idx % dataColors.length]}"
    >&bull; {{ key }}</div>
  </div>
</template>
<style lang="scss" scoped>
.legend {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}
.line-legend {
  flex: 1;
  text-align: center;
  font-size: 12px;
}
</style>
<script>
import constants from "./constants.js";

export default {
  props: {
    dataColors: {
      type: Array,
      default: function() {
        return constants.colorCycle.copy();
      }
    },
    data: {
      type: Object,
      default: function() {
        return {
          xsquared: {
            points: [
              { x: 0, y: 0 },
              { x: 1, y: 1 },
              { x: 2, y: 4 },
              { x: 3, y: 9 },
              { x: 4, y: 16 }
            ]
          }
        };
      }
    }
  }
};
</script>