<template>
  <div>
    <ul class="buttons">
      <li v-for="elem in switchElements" :key="elem.name" class="button">
        <toggle-button
          :disabled="disabled"
          :label="elem.name"
          :value="elem.value == 'On'"
          :busy="thisProperty.state == 'Busy'"
          @input="sendSwitch(elem)"/>
      </li>
    </ul>
  </div>
</template>
<style lang="scss" scoped>
.buttons {
  display: flex;
  padding: 0;
  list-style-type: none;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import ToggleButton from "~/components/basic/ToggleButton.vue";

export default {
  props: ["device", "property", "indiId", "disabled"],
  mixins: [indi],
  components: {
    ToggleButton
  },
  data: function () {
    switches: []
  },
  methods: {
    sendSwitches: function(elemName) {
      this.sendIndiNew(this.thisDevice, this.thisProperty, elemName, "On");
      console.log(`Setting ${elemName} On`);
    },
    sendSwitch: function(element) {
      if (element.value == 'Off') {
        this.sendIndiNew(this.thisDevice, this.thisProperty, element, "On");
        console.log(`Setting ${element.name} On`);
      } else {
        this.sendIndiNew(this.thisDevice, this.thisProperty, element, "Off");
        console.log(`Setting ${element.name} Off`);
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
