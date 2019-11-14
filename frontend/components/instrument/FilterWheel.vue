<template>
  <div class="filter-wheel">
    {{ name }}
    {{ fsmState }}
    <indi-switch-multi-element :disabled="isDisabled" :device="thisDevice" :property="filterNames" ></indi-switch-multi-element>
  </div>
</template>
<style lang="scss" scoped>
</style>
<script>
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import indi from "~/mixins/indi.js";

export default {
  mixins: [indi],
  props: ["device", "indiId"],
  components: {
    IndiSwitchMultiElement
  },
  computed: {
    isDisabled: function () {
      if (!(this.thisDevice && this.thisDevice.properties['fsm'])) { return true; }
      const fsmState = this.thisDevice.properties["fsm"].elements["state"].value;
      return !(fsmState == "READY" || fsmState == "OPERATING") || this.filterNames.state == 'Busy';
    },
    filterNames: function () {
      if (this.thisDevice && this.thisDevice.properties['filterName']) {
        return this.thisDevice.properties['filterName'];
      } else {
        return null;
      }
    },
    name: function () {
      if (this.thisDevice) {
        return name;
      } else {
        return null;
      }
    },
    fsmState: function () {
      if (this.thisDevice && this.thisDevice.properties['fsm']) {
        return this.thisDevice.properties['fsm'].elements['state'].value;
      } else {
        return null;
      }
    }
  }
};
</script>