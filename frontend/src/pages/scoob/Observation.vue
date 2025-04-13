<template>
  <div class="content observation"><div class="view">Placeholder for SCOOB</div></div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.observation {
  margin: $unit;
}
</style>
<script>
import utils from "@/mixins/utils.js";
export default {
  mixins: [utils],
  inject: ["indi"],
}
</script>