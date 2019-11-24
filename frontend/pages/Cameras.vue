<template>
  <div class="controls">
    <div class="cameras">
      <camera-controls-group base-name="sci1"></camera-controls-group>
      <camera-controls-group base-name="sci2"></camera-controls-group>
    </div>
    <div class="coronagraphs">
      <filter-wheel indi-id="fwscind"></filter-wheel>
      <filter-wheel indi-id="fwpupil"></filter-wheel>
      <filter-wheel indi-id="fwfpm"></filter-wheel>
      <filter-wheel indi-id="fwlyot"></filter-wheel>
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
import CameraControlsGroup from "~/components/instrument/CameraControlsGroup.vue";
import FilterWheel from "~/components/instrument/FilterWheel.vue";
import TelescopeSimulator from "~/components/instrument/TelescopeSimulator.vue";

export default {
  components: {
    CameraControlsGroup,
    FilterWheel
  }
};
</script>