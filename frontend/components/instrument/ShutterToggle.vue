<template>
  <toggle-switch
    v-if="thisProperty"
    :value="shutterState"
    @input="changeState"
    :disabled="isDisabled"
    :busy="busy"
    :prompt="true"
    labelOn="open"
    labelOff="shuttered"
  ></toggle-switch>
  <div v-else>
    Waiting for shutter
  </div>
</template>
<style scoped lang="scss">
@use "./css/variables.scss" as *;
</style>
<script>
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import indi from "~/mixins/indi.js";

const components = {
  ToggleSwitch
};

export default {
  components,
  props: ["device", "property", "indiId", "disabled"],
  mixins: [indi],
  methods: {
    changeState: function () {
      let newTarget
      if (this.currentState === "SHUT") {
        newTarget = "OPEN";
      } else if (this.currentState === "OPEN") {
        newTarget = "SHUT";
      } else {
        return;
      }
      this.sendIndiNew(this.thisProperty, this.thisProperty._elements["target"], newTarget);
      // this.busy = true;
      // console.log(`Would have sent ${newTarget}`)
    }
  },
  // watch: {
  //   currentState: function(newValue, oldValue) {
  //     this.busy = false;
  //   }
  // },
  computed: {
    busy() {
      return this.thisProperty.state == 'Busy' || this.currentState == 'UNKNOWN' || this.currentState == 'OFF';
    },
    
    thisProperty() {
      if (!this.thisDevice) return null;
      return this.thisDevice['shutter'];
    },
    currentState: function () {
      if (!this.thisDevice) return null;
      return this.thisProperty._elements["toggle"]._value;
      // return "OPEN";
    },
    shutterState: function () {
      return this.currentState ? "SHUT" : "OPEN";
    },
    isDisabled() {
      console.log(this.thisDevice);
      return this.disabled || this.thisDevice['shutter_status']._elements['status'] == "POWEROFF";
    }
  }
};
</script>