<template>
  <span><toggle-switch
    v-if="thisProperty"
    :value="powerState"
    @input="changeState"
    :disabled="disabled"
    :busy="isBusy"
    :prompt="true"></toggle-switch>
</template>
<style scoped lang="scss">
@import "./css/variables.scss";
</style>
<script>
import CommitButton from "~/components/basic/CommitButton.vue";
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import utils from "~/mixins/utils.js";
import indi from "~/mixins/indi.js";

const components = {
  ToggleSwitch,
  CommitButton
};

export default {
  components,
  props: ["device", "property", "indiId", "disabled"],
  mixins: [indi],
  methods: {
    changeState: function () {
      let newTarget;
      if (this.currentState === "Int") {
        return;
      } else if (this.currentState === "Off") {
        newTarget = "On";
      } else if (this.currentState === "On") {
        newTarget = "Off";
      }
      this.sendIndiNew(this.thisDevice, this.thisProperty, this.thisProperty.elements["target"], newTarget);
    }
  },
  computed: {
    currentState: function () {
      return this.thisProperty.elements["state"].value;
    },
    powerState: function () {
      return this.currentState == "On";
    },
    isBusy: function () {
      return (
        this.thisProperty.state === "Busy" ||
        this.currentState == "Int" ||
        (
          (this.currentState !== this.thisProperty.elements["target"].value)
          &&
          (this.thisProperty.elements["target"].value !== null)
        )
      );
    }
  }
};
</script>