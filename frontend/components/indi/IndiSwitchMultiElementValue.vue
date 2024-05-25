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
      if (this.thisProperty._kind == 'swt') {
        if (!(this.thisProperty.rule == 'OneOfMany')) {
            console.error("Wrong switch rule for IndiSwitchMultiElementValue");
        }
        for (const elName in this.thisProperty._elements) {
            const el = this.thisProperty._elements[elName];
            if (el._value == 'On') {
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