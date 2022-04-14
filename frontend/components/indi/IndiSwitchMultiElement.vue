<template>
  <div>
    <div class="buttons minigrid" :class="{'vertical': orientation == 'vertical', 'horizontal': orientation == 'horizontal'}">
      <toggle-button
        v-for="elem in switchElements" 
        :key="elem.name"
        :disabled="disabled"
        :label="elem.name"
        :value="elem.value == 'On'"
        :busy="thisProperty.state == 'Busy'"
        @input="sendSwitch(elem)"/>
    </div>
  </div>
</template>
<style lang="scss" scoped>
.buttons {
  // display: flex;
  padding: 0;
  &.vertical {
    grid-template-columns: 1fr;
  }
}
</style>
<script>
import indi from "~/mixins/indi.js";
import ToggleButton from "~/components/basic/ToggleButton.vue";
import utils from "~/mixins/utils.js";

export default {
  props: ["device", "property", "indiId", "disabled", "orientation"],
  mixins: [indi, utils],
  components: {
    ToggleButton
  },
  methods: {
    sendSwitch: function(element) {
      if (this.disabled) return;
      if (element.value == 'Off') {
        this.sendIndiNew(this.thisDevice, this.thisProperty, element, "On");
      } else {
        this.sendIndiNew(this.thisDevice, this.thisProperty, element, "Off");
      }
    }
  },
  computed: {
    switchType: function() {
      if (this.thisProperty.rule == "OneOfMany") {
        return "radio";
      } else {
        return "checkbox";
      }
    },
    propertyId: function() {
      if (!(this.thisDevice && this.thisProperty)) return null;
      return this.thisDevice.name + "." + this.thisProperty.name;
    },
    switchElements: function () {
      if (!(this.thisDevice && this.thisProperty)) return null;
      return this.thisProperty.elements;
    },
    selectedSwitches: function() {
      if (!this.thisProperty) return { selectedSwitches: null };
      const enabledSwitches = Object.keys(this.thisProperty.elements).filter(
        key => this.thisProperty.elements[key].value == "On"
      );
      return this.switchType == "checkbox"
        ? enabledSwitches
        : enabledSwitches[0];
    }
  }
};
</script>
