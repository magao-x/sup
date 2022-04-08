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
  props: ["device", "property", "element", "indiId", "onText", "offText"],
  computed: {
    value: function() {
      if (!this.thisElement) return "";
      if (this.thisProperty.kind == 'num') {
        return this.applyFormatString(this.thisElement.format, this.thisElement.value);
      } else if (this.thisProperty.kind == 'swt') {
        let onLabel = 'On', offLabel = 'Off';
        if (typeof this.onText !== "undefined") {
          onLabel = this.onText;
        }
        if (typeof this.offText !== "undefined") {
          offLabel = this.offText;
        }
        return this.thisElement.value == 'On' ? onLabel : offLabel;
      } else {
        return this.thisElement.value;
      }
    }
  }
};
</script>