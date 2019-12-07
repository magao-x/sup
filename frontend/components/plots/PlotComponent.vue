<template>
<div class="plot">
  <plot-axes
    :data="data"
    :dataColors="dataColors"
    :axisColor="axisColor"
    :markerSize="markerSize"
    :timeSeries="timeSeries"
    :numMinutes="numMinutes"
  ></plot-axes>
  <plot-legend :data="data" :dataColors="dataColors"></plot-legend>
</div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.plot {
  display: flex;
  flex-direction: column;
  background: $base02;
  margin: $unit / 2;
  padding: $unit / 2;
  overflow: hidden;
}
</style>
<script>
import PlotAxes from "~/components/plots/PlotAxes.vue";
import PlotLegend from "~/components/plots/PlotLegend.vue";
import constants from "./constants.js";

export default {
  components: {
    PlotAxes,
    PlotLegend
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
    numMinutes: {
      type: Number,
      default: function () { return null; }
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