<template>
  <div class="coronagraph-controls-group">
    <filter-wheel indi-id="fwscind"></filter-wheel>
    <filter-wheel indi-id="fwpupil"></filter-wheel>
    <filter-wheel indi-id="fwfpm"></filter-wheel>
    <filter-wheel indi-id="fwlyot"></filter-wheel>
  </div>
</template>
<style lang="scss" scoped>
@import '~/css/variables.scss';
// .coronagraph-controls-group {
//   display: flex;
// }
</style>
<script>
import FilterWheel from "~/components/instrument/FilterWheel.vue";

export default {
  components: {
    FilterWheel
  }
};
</script>