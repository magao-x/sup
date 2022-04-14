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
  props: ["device", "property", "element", "indiId", "onText", "offText", "placeholder", "formatFunction"],
  computed: {
    value: function() {
      let value;  // assign to value so formatFunction can be applied at end before return
      // if value is missing, show placeholder
      if (!this.thisElement) {
        value = this.placeholder ? this.placeholder : "";
      } else if (this.thisProperty.kind == 'num') {
        // number format functions should receive values to format as numbers
        if (this.formatFunction) {
          return this.formatFunction(this.thisElement.value);
        } else {
          value = this.applyFormatString(this.thisElement.format, this.thisElement.value);
        }
      } else if (this.thisProperty.kind == 'swt') {
        // switches default to On and Off if onText and offText are not given
        // TODO make this a default prop value
        let onLabel = 'On', offLabel = 'Off';
        if (typeof this.onText !== "undefined") {
          onLabel = this.onText;
        }
        if (typeof this.offText !== "undefined") {
          offLabel = this.offText;
        }
        value = this.thisElement.value == 'On' ? onLabel : offLabel;
      } else {
        // "normal" values
        value = this.thisElement.value;
      }
      // apply formatting last (if needed)
      if (this.formatFunction) {
        return this.formatFunction(value);
      } else {
        return value;
      }
    }
  }
};
</script>