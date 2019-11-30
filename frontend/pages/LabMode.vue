<template>
  <div>
    <telescope-simulator></telescope-simulator>
    <basler-camera indiId="camtip"></basler-camera>
    <div class="stages">
      <motion-stage kind="stage" indi-id="stageeyepiece"></motion-stage>
      <motion-stage kind="stage" indi-id="stageadc1"></motion-stage>
      <motion-stage kind="stage" indi-id="stageadc2"></motion-stage>
      <motion-stage kind="stage" indi-id="stagek"></motion-stage>
    </div>
    <camera-controls-group base-name="tip"></camera-controls-group>
  </div>
</template>
<style lang="scss" scoped>
.stages {
  display: flex;
  flex-wrap: wrap;
  .motion-stage {
    min-width: 33%
  }
}
</style>
<script>
import TelescopeSimulator from "~/components/instrument/TelescopeSimulator.vue";
import CameraControlsGroup from "~/components/instrument/CameraControlsGroup.vue";
import BaslerCamera from "~/components/instrument/BaslerCamera.vue";
import MotionStage from "~/components/instrument/MotionStage.vue";

export default {
  components: {
    TelescopeSimulator,
    CameraControlsGroup,
    MotionStage,
    BaslerCamera,
  }
};
</script>