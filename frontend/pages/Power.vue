<template>
  <div class="power view">
    <power-distribution-unit indi-id="pdu0" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="pdu1" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="pdu2" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="pdu3" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="usbdu0" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="usbdu1" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="dcdu0" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="dcdu1" :disabled="disabled"></power-distribution-unit>
  </div>
</template>
<style scoped lang="scss">
@import "./css/variables.scss";
.power {
  margin: $unit;
  padding: $unit;
}
</style>
<script>
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import PowerDistributionUnit from "~/components/instrument/PowerDistributionUnit.vue";
import utils from "~/mixins/utils.js";

const components = {
  PowerDistributionUnit,
  ToggleSwitch
};

export default {
  components,
  data: function () {
    return {controlActive: false};
  },
  computed: {
    disabled: function () {
      return false;
    }
  }
};
</script>