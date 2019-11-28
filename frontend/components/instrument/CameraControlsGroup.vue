<template>
  <div class="camera-controls-group">
    <div class="headerbar">
      <div class="item" style="flex:1">
        <div class="label camera-name">{{ camName }}</div>
        <finite-state-machine-status class="control" :device="cam"></finite-state-machine-status>
      </div>
      <div class="item" style="flex:2">
        <div class="label">shutter</div>
        <shutter-toggle class="control" :device="cam"></shutter-toggle>
      </div>
      <div class="item" style="flex:2">
        <div class="label">writer</div>
        <stream-writer class="control" :device="streamWriter"></stream-writer>
      </div>
    </div>
    <div v-if="isDefined">
      <exposure-time v-if="hasExptime" :device="cam" class="block"></exposure-time>
      <frames-per-second v-if="hasFPS" :device="cam" class="block"></frames-per-second>
      <adc-speed :device="cam"></adc-speed>
      <camera-gain v-if="hasEmgain" :device="cam"></camera-gain>
      <motion-stage preset-base-name="filter" :device="fw" :label="fwName"></motion-stage>
      <motion-stage preset-base-name="preset" :device="stage"></motion-stage>
      <region-of-interest v-if="hasROI" :device="cam"></region-of-interest>
    </div>
    <div v-else>
      <p>Waiting for device</p>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';

.block {
  border: 1px solid $primary;
}

.headerbar {
  display: flex;
  .item {
    flex: 1;
    margin: 0.25em;
    display: flex;
    flex-direction: column;
  }
  .label {
    font-weight: bold;
    text-align: center;
    padding-right: 2 * $unit;
    &.camera-name {
      text-align: left;
    }
  }
  .control {
    font-size: 14px;
  }
}
.camera-controls-group {
  background: $base02;
  padding: $unit;
  &:first-child {
    margin-top: 0;
  }
  margin: $unit;
}
</style>
<script>
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import MotionStage from "~/components/instrument/MotionStage.vue";
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";
import RegionOfInterest from "~/components/instrument/RegionOfInterest.vue";
import StreamWriter from "~/components/instrument/StreamWriter.vue";
import ShutterToggle from "~/components/instrument/ShutterToggle.vue";
import ExposureTime from "~/components/instrument/ExposureTime.vue";
import FramesPerSecond from "~/components/instrument/FramesPerSecond.vue";
import AdcSpeed from "~/components/instrument/AdcSpeed.vue";
import CameraGain from "~/components/instrument/CameraGain.vue";

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
    MotionStage,
    RegionOfInterest,
    StreamWriter,
    ShutterToggle,
    FiniteStateMachineStatus,
    ExposureTime,
    FramesPerSecond,
    AdcSpeed,
    CameraGain
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
    },
    hasEmgain() {
      return this.isDefined && this.cam.properties.hasOwnProperty('emgain');
    },
    hasFPS() {
      return this.isDefined && this.cam.properties.hasOwnProperty('fps');
    },
    hasExptime() {
      return this.isDefined && this.cam.properties.hasOwnProperty('exptime');
    },
    hasROI() {
      return this.isDefined && this.cam.properties.hasOwnProperty('roi_bin_x');
    }
  }
};
</script>