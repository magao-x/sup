<template>
  <div class="controls">
    <div class="cameras">
      <camera-controls-group base-name="sci1"></camera-controls-group>
      <camera-controls-group base-name="sci2"></camera-controls-group>
    </div>
    <div class="coronagraphs">
      <motion-stage preset-base-name="filter" indi-id="fwscind"></motion-stage>
      <motion-stage preset-base-name="filter" indi-id="fwpupil"></motion-stage>
      <motion-stage preset-base-name="filter" indi-id="fwfpm"></motion-stage>
      <motion-stage preset-base-name="filter" indi-id="fwlyot"></motion-stage>
      <motion-stage preset-base-name="preset" indi-id="stagescibs"></motion-stage>
    </div>
  </div>
</template>
<style lang="scss" scoped>
.controls {
  width: 100%;
  display: flex;
  .cameras, .coronagraphs {
    flex: 1;
    max-width: 50%;
  }
}
</style>
<script>
// TODO: separate coronagraph gui group for pupil, then fpm, then lyot
import CameraControlsGroup from "~/components/instrument/CameraControlsGroup.vue";
import MotionStage from "~/components/instrument/MotionStage.vue";
import TelescopeSimulator from "~/components/instrument/TelescopeSimulator.vue";

export default {
  components: {
    CameraControlsGroup,
    MotionStage
  }
};
</script>