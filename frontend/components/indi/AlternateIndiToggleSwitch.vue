<template>
  <span v-if="indiDefined" @click="toggle" :class="{'glowy': switchValue && disabled}">
    <span class="label-text">{{ label }}</span>
    <!-- <input type="checkbox" :disabled="switchDisabled"
      :checked="switchValue" @input="toggle"> -->
      <material-icon v-if="switchValue" name="check_box"></material-icon>
      <material-icon v-else name="check_box_outline_blank"></material-icon>
  </span>
  <span v-else>?</span>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.glowy {
  text-shadow: 0 0 5 $plasma-blue; /* Initial shadow */
  animation: pulse 1s infinite alternate; /* Animation */
  color: $plasma-blue;
}

@keyframes pulse {
  0% {
    text-shadow: 0 0 5px $plasma-blue; /* Initial shadow */
  }
  100% {
    text-shadow: 0 0 20px $plasma-blue; /* Pulsing shadow */
  }
}

</style>
<script>
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import MaterialIcon from "~/components/basic/MaterialIcon.vue";
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  mixins: [indi, utils],
  components: {
    ToggleSwitch,
    MaterialIcon
  },
  props: {
    device: Object,
    property: Object,
    element: Object,
    indiId: String,
    label: String,
    disabled: {
      type: Boolean,
      default: () => false,
    }
  },
  methods: {
    toggle: function () {
      if (this.switchBusy) return;
      this.indi.sendIndiNewByNames(this.thisDeviceName, this.thisProperty.name, this.thisElement.name, !this.switchValue ? 'On' : 'Off');
    }
  },
  computed: {
    switchBusy: function () {
      return this.disabled || !this.thisProperty || this.switchValue === null || this.thisProperty.state == "Busy" || this.thisProperty.state == "Alert";
    },
    switchDisabled: function () {
      if (!this.thisProperty) return true;
      return this.thisProperty.perm == 'ro' || this.disabled;
    },
    switchValue: function () {
      return this.thisElement && this.thisElement._value == 'On';
    }
  }
};
</script>