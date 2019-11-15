<template>
  <div class="controls">
    <div class="cameras">
      <camera-controls-group base-name="sci1"></camera-controls-group>
      <camera-controls-group base-name="sci2"></camera-controls-group>
      <camera-controls-group base-name="lowfs"></camera-controls-group>
    </div>
    <div class="coronagraphs">
      <coronagraph-controls-group></coronagraph-controls-group>
    </div>
  </div>
</template>
<style lang="scss" scoped>
.controls {
  width: 100%;
  display: flex;
  .cameras {
    flex: 1;
  }
}
</style>
<script>
// TODO: separate coronagraph gui group for pupil, then fpm, then lyot
import CameraControlsGroup from "~/components/instrument/CameraControlsGroup.vue";
import CoronagraphControlsGroup from "~/components/instrument/CoronagraphControlsGroup.vue";
import TelescopeSimulator from "~/components/instrument/TelescopeSimulator.vue";

export default {
  components: {
    CameraControlsGroup,
    CoronagraphControlsGroup
  }
};
</script>