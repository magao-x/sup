<template>
  <plot-component :data="plotData" :timeSeries="true" :numMinutes="numMinutes"></plot-component>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;
</style>
<script>
import Vue from "vue";
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";
import constants from "@/constants.js";
import PlotComponent from "@/components/plots/PlotComponent.vue";
import { DateTime } from "luxon";

export default {
  mixins: [indi, utils],
  props: ["device", "property", "element", "indiId"],
  components: {
    PlotComponent
  },
  data() {
    return {
      recordedPlotData: {},
      numMinutes: constants.plots.numMinutes,
    }
  },
  inject: ['time'],
  methods: {
    fullIndiId(element) {
      return `${this.thisDeviceName}.${this.thisProperty.name}.${element.name}`;
    },
    recordPoints() {
      if (!this.indiDefined) return;
      for (let element of this._elements) {
        const fullId = this.fullIndiId(element);
        if (!this.recordedPlotData[fullId]) {
          // initialize recorded data as reactive property
          Vue.set(this.recordedPlotData, fullId, {points: []});
        }
        const eltData = this.recordedPlotData[fullId];
        // append to recorded data (only if we're getting good data)
        if (this.connectionStatus) {
          eltData.points.push({x: this.time.currentTime, y: element._value})
        }
        // expire old data
        const filterOutdated = function (value) {
          const diffMinutes = value.x.diffNow('minutes').minutes;
          return Math.abs(diffMinutes) < constants.plots.numMinutes;
        };
        eltData.points = eltData.points.filter(filterOutdated);
      }
      return this.recordedPlotData;
    }
  },
  computed: {
    elements() {
      if (this.indiDefined && this.thisProperty && this.thisElement) {
        return [this.thisElement];
      } else if (this.indiDefined && this.thisProperty) {
        return Object.keys(this.thisProperty._elements).map(k => this.thisProperty._elements[k]);
      } else {
        return [];
      }
    },
    plotData: function() {
      if (!this.indiDefined || Object.keys(this.recordedPlotData).length != this._elements.length) {
        return {waiting: {points: []}};
      } else {
        return this.recordedPlotData;
      }
    }
  },
  mounted: function() {
    this.updateInterval = window.setInterval(this.recordPoints, 1000);
    this.recordPoints();
  },
  beforeUnmount: function() {
    window.clearInterval(this.updateInterval);
  }
};
</script>