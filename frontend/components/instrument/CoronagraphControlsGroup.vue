<template>
  <div class="coronagraph-controls-group">
    <filter-wheel indi-id="fwpupil" orientation="vertical"></filter-wheel>
    <filter-wheel indi-id="fwfpm" orientation="vertical"></filter-wheel>
    <filter-wheel indi-id="fwlyot" orientation="vertical"></filter-wheel>
  </div>
</template>
<style lang="scss" scoped>
@import '~/css/variables.scss';
.coronagraph-controls-group {
  display: flex;
}
</style>
<script>
import FilterWheel from "~/components/instrument/FilterWheel.vue";

export default {
  components: {
    FilterWheel
  }
};
</script>