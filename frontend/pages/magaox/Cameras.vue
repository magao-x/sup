<template>
    <div class="cols">
      <div class="col">
        <camera-controls-group base-name="sci1"></camera-controls-group>
        <camera-controls-group base-name="sci2"></camera-controls-group>
      </div>
      <div class="col">
        <div style="display: flex" v-if="indiIdExists('flipacq.presetName')">
          <div>Acquisition camera flip mirror:</div>
          <indi-switch-multi-element indi-id="flipacq.presetName"></indi-switch-multi-element>
        </div>
        <div v-else>
          Waiting for acquisition camera
        </div>
        <motion-stage kind="filterwheel" indi-id="fwscind"></motion-stage>
        <motion-stage kind="filterwheel" indi-id="fwpupil"></motion-stage>
        <motion-stage kind="filterwheel" indi-id="fwfpm"></motion-stage>
        <motion-stage kind="filterwheel" indi-id="fwlyot"></motion-stage>
        <motion-stage kind="stage" indi-id="stagescibs"></motion-stage>
      </div>
    </div>
</template>
<style lang="scss" scoped>
@use "./css/variables.scss" as *;
.controls {
  width: 100%;
}
</style>
<script>
// TODO: separate coronagraph gui group for pupil, then fpm, then lyot
import CameraControlsGroup from "~/components/instrument/CameraControlsGroup.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import MotionStage from "~/components/instrument/MotionStage.vue";
import ObserverControl from "~/components/instrument/ObserverControl.vue";
import utils from "~/mixins/utils.js";
import TelescopeSimulator from "~/components/instrument/TelescopeSimulator.vue";

export default {
  mixins: [utils],
  components: {
    CameraControlsGroup,
    IndiSwitchMultiElement,
    MotionStage,
    ObserverControl
  }
};
</script>