<template>
  <toggle-switch
    :value="switchValue"
    :busy="switchBusy"
    :disabled="switchDisabled"
    :readOnly="switchReadOnly"
    :prompt="false"
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
import utils from "~/mixins/utils.js";

export default {
  mixins: [indi, utils],
  components: {
    ToggleSwitch
  },
  props: {
    device: Object,
    property: Object,
    element: Object,
    indiId: String,
    disabled: Boolean,
    labelOn: {
      type: String,
      default: () => 'On',
    },
    labelOff: {
      type: String,
      default: () => 'Off',
    },
    readOnly: {
      type: Boolean,
      default: false,
    }
  },
  data: function () {
      return {
          pendingUpdate: false,

      }
  },
  methods: {
    toggle: function() {
      if (this.switchBusy) return;
      this.indi.sendIndiNewByNames(this.thisDeviceName, this.thisProperty.name, this.thisElement.name, !this.switchValue ? 'On' : 'Off');
      this.pendingUpdate = true;
    }
  },
  watch: {
      switchValue (newValue, oldValue) {
          this.pendingUpdate = false;
      }
  },
  computed: {
    switchBusy: function () {
      return this.switchDisabled || !this.thisProperty || this.switchValue === null || this.thisProperty.state == "Busy" || this.thisProperty.state == "Alert" || this.pendingUpdate;
    },
    switchReadOnly() {
      return this.readOnly || (this.indiDefined && (this.thisProperty?.perm == 'ro'));
    },
    switchDisabled: function () {
      if (!this.thisProperty) return true;
      return this.disabled;
    },
    switchValue: function () {
      return this.thisElement && this.thisElement._value == 'On';
    }
  }
};
</script>