<template>
  <toggle-switch :value="switchValue" :busy="switchBusy" :disabled="switchDisabled" @input="toggle"></toggle-switch>
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
  props: ["device", "property", "element", "indiId"],
  // watch: {
  //   element: function (newValue, oldValue) {
  //     this.switchValue = newValue.value == 'On';
  //   }
  // },
  // data: function () {
  //   return {
  //     switchValue: this.thisElement ? this.thisElement.value == 'On' : false
  //   }
  // },
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