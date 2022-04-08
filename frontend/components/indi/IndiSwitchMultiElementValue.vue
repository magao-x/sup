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
  props: ["device", "property", "indiId"],
  computed: {
    value: function() {
      if (!this.thisProperty) return "";
      if (this.thisProperty.kind == 'swt') {
        if (!(this.thisProperty.rule == 'OneOfMany')) {
            console.error("Wrong switch rule for IndiSwitchMultiElementValue");
        }
        for (const elName in this.thisProperty.elements) {
            const el = this.thisProperty.elements[elName];
            if (el.value == 'On') {
                return el.label ? el.label : el.name;
            }
        }
        return '?';
      } else {
        console.error("Trying to use IndiSwitchMultiElementValue on a non-switch property", this.thisProperty);
      }
    }
  }
};
</script>