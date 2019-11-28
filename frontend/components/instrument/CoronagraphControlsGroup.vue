<template>
  <div class="coronagraph-controls-group">
    <motion-stage preset-base-name="filter" indi-id="fwscind"></filter-wheel>
    <motion-stage preset-base-name="filter" indi-id="fwpupil"></filter-wheel>
    <motion-stage preset-base-name="filter" indi-id="fwfpm"></filter-wheel>
    <motion-stage preset-base-name="filter" indi-id="fwlyot"></filter-wheel>
  </div>
</template>
<style lang="scss" scoped>
@import '~/css/variables.scss';
// .coronagraph-controls-group {
//   display: flex;
// }
</style>
<script>
import MotionStage from "~/components/instrument/MotionStage.vue";

export default {
  components: {
    MotionStage
  }
};
</script>