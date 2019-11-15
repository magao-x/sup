<template>
  <toggle-switch
    v-if="thisProperty"
    :value="shutterState"
    @input="changeState"
    :disabled="disabled"
    :busy="busy"></toggle-switch>
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
  data: function () {
    return {
      busy: false
    };
  },
  methods: {
    changeState: function () {
      let newTarget
      if (this.currentState === "SHUT") {
        newTarget = "OPEN";
      } else if (this.currentState === "OPEN") {
        newTarget = "SHUT";
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
    currentState: function () {
      return this.thisProperty.elements["current"].value;
    },
    shutterState: function () {
      return this.currentState == "OPEN";
    }
  }
};
</script>