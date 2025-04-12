<template>
  <div class="camera-controls-group view">
    <div class="header">
      <div class="camera-name">
        <span class="label">{{ camName }}</span>
        <finite-state-machine-status class="control" :device="cam"></finite-state-machine-status>
      </div>
      <indi-toggle-switch
        v-if="hasShutter"
        class="control"
        :indi-id="`${camName}.shutter.toggle`"
        label-off="open"
        label-on="shut"
      ></indi-toggle-switch>
      <indi-toggle-switch
        v-if="streamWriter"
        class="control"
        :indi-id="`${streamWriterName}.writing.toggle`"
        label-off="paused"
        label-on="writing"
      ></indi-toggle-switch>
    </div>
    <div v-if="isDefined && baseName !== 'wfs'">
      <div class="flex-row">
        <div class="block" v-if="hasExptime || hasADCSpeed">
          <exposure-time v-if="hasExptime" :device="cam"></exposure-time>
          <adc-speed v-if="hasADCSpeed" :device="cam"></adc-speed>
        </div>
        <div style="min-width: 15em;">
          <!-- <region-of-interest v-if="hasROI" class="block" :device="cam"></region-of-interest> -->
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
      <div style="min-width: 400px;">CCD temperature: <indi-property :device="cam" :property="cam['temp_ccd']"></indi-property></div>
      <div v-if="cam['temp_control']">Temperature control: <indi-value :device="cam" :property="cam['temp_control']" :element="cam['temp_control']._elements['status']"></indi-value></div>
    </div>
    <div v-if="isDefined && baseName !== 'wfs'">
      <motion-stage v-if="fw" kind="filterwheel" :device="fw" :label="fwName" class="block"></motion-stage>
      <motion-stage v-if="stage" kind="stage" :device="stage" class="block"></motion-stage>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@use '~/css/variables.scss' as *;

.header {
  display: flex;
  & > * {
    flex: 1;
  }
  & > .camera-name {
    flex: 0;
    min-width: 7em;
  }
}

.block {
  // border: 1px solid $plasma-blue;
  padding: $unit;
}

.camera-controls-group {
  background: var(--inset-bg);
  padding: $unit;
  overflow: hidden;
  &:first-child {
    margin-top: 0;
  }
  
}
</style>
<script>
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiToggleSwitch from "~/components/indi/IndiToggleSwitch.vue";
import MotionStage from "~/components/instrument/MotionStage.vue";
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";
// import RegionOfInterest from "~/components/instrument/RegionOfInterest.vue";
import WavefrontSensor from "~/components/instrument/WavefrontSensor.vue";
import StreamWriter from "~/components/instrument/StreamWriter.vue";
import ShutterToggle from "~/components/instrument/ShutterToggle.vue";
import ExposureTime from "~/components/instrument/ExposureTime.vue";
import FramesPerSecond from "~/components/instrument/FramesPerSecond.vue";
import AdcSpeed from "~/components/instrument/AdcSpeed.vue";
import CameraGain from "~/components/instrument/CameraGain.vue";
import PowerToggle from './PowerToggle.vue';

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
    // RegionOfInterest,
    StreamWriter,
    IndiToggleSwitch,
    FiniteStateMachineStatus,
    ExposureTime,
    FramesPerSecond,
    AdcSpeed,
    CameraGain,
    WavefrontSensor,
    IndiProperty,
    IndiValue,
    PowerToggle,
  },
  inject: ["indi"],
  computed: {
    camName() {
      return "cam" + this.baseName;
    },
    cam() {
      return this.indi.world[this.camName];
    },
    fwName() {
      return "fw" + this.baseName;
    },
    fw() {
      return this.indi.world[this.fwName];
    },
    stageName() {
      return "stage" + this.baseName;
    },
    stage() {
      return this.indi.world[this.stageName];
    },
    streamWriterName() {
      return this.camName + "-sw";
    },
    streamWriter() {
      return this.indi.world[this.streamWriterName];
    },
    isDefined() {
      return typeof this.indi.world[this.camName] !== "undefined";
    },
    hasEmgain() {
      return this.isDefined && this.cam.hasOwnProperty('emgain');
    },
    hasShutter() {
      return this.isDefined && this.cam.hasOwnProperty('shutter');
    },
    hasFPS() {
      return this.isDefined && this.cam.hasOwnProperty('fps');
    },
    hasExptime() {
      return this.isDefined && this.cam.hasOwnProperty('exptime');
    },
    hasADCSpeed() {
      return this.isDefined && this.cam.hasOwnProperty('adcspeed');
    },
    hasROI() {
      return this.isDefined && this.cam.hasOwnProperty('roi_bin_x');
    }
  }
};
</script>
