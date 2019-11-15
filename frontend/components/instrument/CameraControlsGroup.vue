<template>
  <div class="camera-controls-group">
    <h1 class="camera-name">{{ camName }}</h1>
    <div v-if="isDefined">
      <filter-wheel :device="fw" :label="fwName"></filter-wheel>
      <filter-wheel indi-id="fwscind"></filter-wheel> <!--todo goes with camscis-->
      <focus-stage :device="stage"></focus-stage>
      <region-of-interest :device="cam"></region-of-interest>
      <stream-writer :device="streamWriter"></stream-writer>
      <shutter-toggle :device="cam"></shutter-toggle>
    </div>
    <div v-else>
      <p>Waiting for device</p>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';
.camera-controls-group {
  background: $base02;
  padding: $unit;
  min-width: 30em;
  &:first-child {
    margin-top: 0;
  }
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
import FocusStage from "~/components/instrument/FocusStage.vue";
import RegionOfInterest from "~/components/instrument/RegionOfInterest.vue";
import StreamWriter from "~/components/instrument/StreamWriter.vue";
import ShutterToggle from "~/components/instrument/ShutterToggle.vue";

const cameraGroup = {
  filterWheel: null,
  focusStage: null,
  exposureTime: null,
  adcSpeed: null,
  gain: null,
  regionOfInterest: null,
  streamWriter: null,
  shutter: null
};
export default {
  props: ["baseName"],
  components: {
    IndiSwitchMultiElement,
    FilterWheel,
    FocusStage,
    RegionOfInterest,
    StreamWriter,
    ShutterToggle,
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
      return this.camName + "-sw";
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