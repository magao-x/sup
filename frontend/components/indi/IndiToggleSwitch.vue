<template>
  <toggle-switch
    :value="switchValue"
    :busy="switchBusy"
    :disabled="switchDisabled"
    :prompt="prompt"
    :labelOn="labelOn"
    :labelOff="labelOff"
    @input="toggle"
  ></toggle-switch>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
</style>
<script>
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import indi from "~/mixins/indi.js";

export default {
  mixins: [indi],
  components: {
    ToggleSwitch
  },
  props: {
    device: Object,
    property: Object,
    element: Object,
    indiId: String,
    labelOn: {
      type: String,
      default: () => 'On',
    },
    labelOff: {
      type: String,
      default: () => 'Off',
    },
    prompt: {
      type: Boolean,
      default: () => false
    },
  },
  methods: {
    toggle: function() {
      if (this.switchBusy) return;
      this.$socket.emit('indi_new', {
          'device': this.thisDevice.name,
          'property': this.thisProperty.name,
          'element': this.thisElement.name,
          'value': !this.switchValue ? 'On' : 'Off'
      });
    }
  },
  computed: {
    switchBusy: function () {
      if (!this.thisProperty) return true;
      return this.switchValue === null || this.thisProperty.state == "Busy" || this.thisProperty.state == "Alert";
    },
    switchDisabled: function () {
      if (!this.thisProperty) return true;
      return this.thisProperty.perm == 'ro';
    },
    switchValue: function () {
      return this.thisElement.value == 'On';
    }
  }
};
</script>