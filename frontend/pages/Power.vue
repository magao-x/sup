<template>
  <div>
    <div>Power control enabled: <toggle-switch v-model="controlActive"></toggle-switch></div>
    <power-distribution-unit indiId="pdu0" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="pdu1" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="pdu2" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="pdu3" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="usbdu0" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="dcdu0" :disabled="disabled"></power-distribution-unit>
    <power-distribution-unit indi-id="dcdu1" :disabled="disabled"></power-distribution-unit>
  </div>
</template>
<style scoped lang="scss">
@import "./css/variables.scss";
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
    return {controlActive: true};
  },
  computed: {
    disabled: function () {
      return this.controlActive !== true;
    }
  }
};
</script>