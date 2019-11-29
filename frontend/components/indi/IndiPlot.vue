<template>
  <plot-component :data="plotData" :timeSeries="true"></plot-component>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import PlotComponent from "~/components/plots/PlotComponent.vue";

export default {
  mixins: [indi, utils],
  props: ["device", "property", "element", "indiId"],
  components: {
    PlotComponent
  },
  methods: {
    fullIndiId(element) {
      return `${this.thisDevice.name}.${this.thisProperty.name}.${element.name}`;
    }
  },
  computed: {
    plotData: function() {
      if (!this.thisElement && !this.thisProperty) return {waiting: {points: []}};
      let elements;
      if (!this.thisElement) {
        elements = Object.keys(this.thisProperty.elements).map(k => this.thisProperty.elements[k]);
      } else {
        elements = [this.thisElement];
      }
      let data = {};
      for (let element of elements) {
        console.log(element);
        let values = element.history.values;
        data[this.fullIndiId(element)] = {
          points: element.history.times.map((val, idx) => {return {x: val, y: values[idx]}}),
        };
      }
      return data;
    }
  }
};
</script>