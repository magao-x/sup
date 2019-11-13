<template>
  <div class="controls">
    <camera-controls-group base-name="sci1"></camera-controls-group>
    <camera-controls-group base-name="sci2"></camera-controls-group>
  </div>
</template>
<style lang="scss" scoped>
.controls {
  width: 100%;
}
</style>
<script>
// TODO: separate coronagraph gui group for pupil, lyot, fpm
import CameraControlsGroup from "~/components/instrument/CameraControlsGroup.vue";
export default {
  components: {
    CameraControlsGroup
  }
};
</script>