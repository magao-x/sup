<template>
  <div class="coronagraph-controls-group">
    <filter-wheel indi-id="fwpupil"></filter-wheel>
    <filter-wheel indi-id="fwfpm"></filter-wheel>
    <filter-wheel indi-id="fwlyot"></filter-wheel>
  </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';
.camera-controls-group {
  background: $base02;
  padding: $unit;
  h1.camera-name {
    font-size: inherit;
    padding: 0 0 $unit 0;
    margin: 0;
  }
  margin: $unit;
}
</style>
<script>
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import FilterWheel from "~/components/instrument/FilterWheel.vue";

const cameraGroup = {
  filterWheel: null,
  focusStage: null,
  exposureTime: null,
  adcSpeed: null,
  gain: null,
  regionOfInterest: null,
  streamWriter: null
};
export default {
  props: ["baseName"],
  components: {
    IndiSwitchMultiElement,
    FilterWheel
  },
  computed: {
    camName() {
      return "cam" + this.baseName;
    },
    cam() {
      return this.$store.state.devices[this.camName];
    },
    fwName() {
      return "fw" + this.baseName;
    },
    fw() {
      return this.$store.state.devices[this.fwName];
    },
    stageName() {
      return "stage" + this.baseName;
    },
    stage() {
      return this.$store.state.devices[this.stageName];
    },
    streamWriterName() {
      return "sw" + this.baseName;
    },
    streamWriter() {
      return this.$store.state.devices[this.streamWriterName];
    },
    isDefined() {
      return typeof this.$store.state.devices[this.camName] !== "undefined";
    }
  }
};
</script>