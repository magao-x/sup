<template>
  <plot-axes
    :data="data"
    :dataColors="dataColors"
    :axisColor="axisColor"
    :markerSize="markerSize"
    :timeSeries="timeSeries"
  ></plot-axes>
</template>
<style lang="scss" scoped>
</style>
<script>
import PlotAxes from "~/components/plots/PlotAxes.vue";
import constants from "./constants.js";

export default {
  components: {
    PlotAxes
  },
  props: {
    dataColors: {
      type: Array,
      default: function() {
        return constants.colorCycle;
      }
    },
    axisColor: {
      type: String,
      default: function() {
        return constants.axisColor;
      }
    },
    markerSize: {
      type: Number,
      default: function() {
        return 2;
      }
    },
    timeSeries: {
      type: Boolean,
      default: function() {
        return false;
      }
    },
    showLegend: {
      type: Boolean,
      default: function() {
        return true;
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