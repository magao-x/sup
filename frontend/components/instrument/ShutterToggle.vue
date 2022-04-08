<template>
  <toggle-switch
    v-if="thisProperty"
    :value="shutterState"
    @input="changeState"
    :disabled="disabled"
    :busy="busy"
    :prompt="true"
    labelOn="SHUT"
    labelOff="OPEN"
  ></toggle-switch>
  <div v-else>
    Waiting for shutter
  </div>
</template>
<style scoped lang="scss">
@import "./css/variables.scss";
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
      this.sendIndiNew(this.thisDevice, this.thisProperty, this.thisProperty.elements["target"], newTarget);
      this.busy = true;
      // console.log(`Would have sent ${newTarget}`)
    }
  },
  watch: {
    currentState: function(newValue, oldValue) {
      this.busy = false;
    }
  },
  computed: {
    busy() {
      return this.thisProperty.state == 'Busy' || this.currentState == 'UNKNOWN' || this.currentState == 'OFF';
    },
    thisProperty() {
      if (!this.thisDevice) return null;
      return this.thisDevice.properties['shutter'];
    },
    currentState: function () {
      if (!this.thisDevice) return null;
      return this.thisProperty.elements["toggle"].value;
      // return "OPEN";
    },
    shutterState: function () {
      return this.currentState ? "SHUT" : "OPEN";
    }
  }
};
</script>