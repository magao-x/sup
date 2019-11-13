<template>
  <span>{{ value }}</span>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
</style>
<script>
import indi from "~/mixins/indi.js";

export default {
  mixins: [indi],
  props: ["device", "property", "element", "indiId"],
  computed: {
    value: function() {
      return this.thisElement.value;
    }
  }
};
</script>