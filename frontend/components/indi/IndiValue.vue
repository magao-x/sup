<template>
  <span>{{ value }}</span>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  mixins: [indi, utils],
  props: ["device", "property", "element", "indiId"],
  computed: {
    value: function() {
      if (!this.thisElement) return "";
      if (this.thisProperty.kind == 'num') {
        return this.applyFormatString(this.thisElement.format, this.thisElement.value);
      } else {
        return this.thisElement.value;
      }
    }
  }
};
</script>