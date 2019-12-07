<template>
  <div class="camera-controls-group">
    <div class="headerbar">
      <div class="item" style="flex:1">
        <div class="label camera-name">{{ camName }}</div>
        <finite-state-machine-status class="control" :device="cam"></finite-state-machine-status>
      </div>
      <div v-if="hasShutter" class="item" style="flex:2">
        <div class="label">shutter</div>
        <shutter-toggle class="control" :device="cam"></shutter-toggle>
      </div>
      <div v-if="streamWriter" class="item" style="flex:2">
        <div class="label">writer</div>
        <stream-writer class="control" :device="streamWriter"></stream-writer>
      </div>
    </div>

    <div v-if="isDefined && baseName !== 'wfs'">
      <div class="flex-row">
        <div class="block" v-if="hasExptime || hasADCSpeed">
          <exposure-time v-if="hasExptime" :device="cam"></exposure-time>
          <adc-speed v-if="hasADCSpeed" :device="cam"></adc-speed>
        </div>
        <div style="min-width: 15em;">
          <region-of-interest v-if="hasROI" class="block"></region-of-interest>
        </div>
      </div>
      <frames-per-second v-if="hasFPS" :device="cam" class="block"></frames-per-second>
      <camera-gain v-if="hasEmgain" :device="cam" class="block"></camera-gain>
    </div>
    <wavefront-sensor v-else-if="isDefined && baseName === 'wfs'" :device="cam"></wavefront-sensor>
    <div v-else>
      <p>Waiting for device</p>
    </div>
    <div v-if="isDefined" class="flex-row block">
      <div style="min-width: 400px;">CCD temperature: <indi-property :device="cam" :property="cam.properties['temp_ccd']"></indi-property></div>
      <div v-if="cam.properties['temp_control']">Temperature control: <indi-value :device="cam" :property="cam.properties['temp_control']" :element="cam.properties['temp_control'].elements['status']"></indi-value></div>
    </div>
    <div v-if="isDefined && baseName !== 'wfs'">
      <motion-stage v-if="fw" kind="filterwheel" :device="fw" :label="fwName" class="block"></motion-stage>
      <motion-stage v-if="stage" kind="stage" :device="stage" class="block"></motion-stage>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';

.block {
  // border: 1px solid $primary;
  padding: $unit;
}

.headerbar {
  display: flex;
  border-bottom: 1px solid;
  .item {
    flex: 1;
    margin: 0.25em;
    display: flex;
    flex-direction: column;
  }
  .label {
    font-weight: bold;
    padding-right: 2 * $unit;
  }
  .control {
    font-size: 14px;
  }
}
.camera-controls-group {
  background: $base02;
  padding: $unit;
  overflow: hidden;
  &:first-child {
    margin-top: 0;
  }
  margin: $unit;
}
</style>
<script>
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import MotionStage from "~/components/instrument/MotionStage.vue";
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";
import RegionOfInterest from "~/components/instrument/RegionOfInterest.vue";
import WavefrontSensor from "~/components/instrument/WavefrontSensor.vue";
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
    CameraGain,
    WavefrontSensor,
    IndiProperty,
    IndiValue,
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
    hasShutter() {
      return this.isDefined && this.cam.properties.hasOwnProperty('shutter');
    },
    hasFPS() {
      return this.isDefined && this.cam.properties.hasOwnProperty('fps');
    },
    hasExptime() {
      return this.isDefined && this.cam.properties.hasOwnProperty('exptime');
    },
    hasADCSpeed() {
      return this.isDefined && this.cam.properties.hasOwnProperty('adcspeed');
    },
    hasROI() {
      return this.isDefined && this.cam.properties.hasOwnProperty('roi_bin_x');
    }
  }
};
</script>