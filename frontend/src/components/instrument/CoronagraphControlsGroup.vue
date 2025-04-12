<template>
  <div class="coronagraph-controls-group">
    <motion-stage kind="filterwheel" indi-id="fwscind"></motion-stage>
    <motion-stage kind="filterwheel" indi-id="fwpupil"></motion-stage>
    <motion-stage kind="filterwheel" indi-id="fwfpm"></motion-stage>
    <motion-stage kind="filterwheel" indi-id="fwlyot"></motion-stage>
  </div>
</template>
<style lang="scss" scoped>
@use '@/css/variables.scss' as *;
// .coronagraph-controls-group {
//   display: flex;
// }
</style>
<script>
import MotionStage from "@/components/instrument/MotionStage.vue";

export default {
  components: {
    MotionStage
  }
};
</script>