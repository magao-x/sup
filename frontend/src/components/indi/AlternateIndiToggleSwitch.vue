<template>
  <div v-if="indiDefined" @click="toggle" :class="{'glowy': switchValue && disabled, 'stacked': stacked}">
    <span v-if="label" class="label-text stackable">{{ label }}</span>
    <material-icon v-if="switchValue && !disabled" name="check_box" class="stackable"></material-icon>
    <material-icon v-else-if="!switchValue && !disabled" name="check_box_outline_blank" class="stackable"></material-icon>
    <material-icon v-else-if="switchValue && disabled" name="power_settings_new" class="stackable"></material-icon>
    <material-icon v-else-if="!switchValue && disabled" name="more_horiz" class="stackable"></material-icon>
  </div>
  <div v-else>?</div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.glowy {
  text-shadow: 0 0 5 $plasma-blue; /* Initial shadow */
  animation: pulse 1s infinite alternate; /* Animation */
  color: $plasma-blue;
}

.stacked {
  .stackable {
    display: block;
    margin: 0.25rem;
  }
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
import ToggleSwitch from "@/components/basic/ToggleSwitch.vue";
import MaterialIcon from "@/components/basic/MaterialIcon.vue";
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";

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
    },
    stacked: {
      type: Boolean,
      default: () => false,
    },
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