<template>
  <div class="controls">
    <div class="cameras">
      <camera-controls-group base-name="wfs"></camera-controls-group>
      <camera-controls-group base-name="lowfs"></camera-controls-group>
      <camera-controls-group base-name="tip"></camera-controls-group>
    </div>
    <div class="coronagraphs">
      <motion-stage indi-id="fwpupil" kind="filterwheel"></motion-stage>
      <div v-if="indiIdExists('fliptip.position')">Pupil viewing flip mirror:
        <indi-switch-multi-element indi-id="fliptip.position"></indi-switch-multi-element></div>
      <div v-else>
        Waiting for fliptip.position
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
.controls {
  width: 100%;
  display: flex;
  .cameras,.coronagraphs {
    flex: 1;
    max-width: 50%;
  }
}
</style>
<script>
// TODO: separate coronagraph gui group for pupil, then fpm, then lyot
import CameraControlsGroup from "@/components/instrument/CameraControlsGroup.vue";
import MotionStage from "@/components/instrument/MotionStage.vue";
import TelescopeSimulator from "@/components/instrument/TelescopeSimulator.vue";
import IndiSwitchMultiElement from "@/components/indi/IndiSwitchMultiElement.vue";
import utils from "@/mixins/utils.js";

export default {
  mixins: [utils],
  components: {
    CameraControlsGroup,
    MotionStage,
    IndiSwitchMultiElement
  }
};
</script>