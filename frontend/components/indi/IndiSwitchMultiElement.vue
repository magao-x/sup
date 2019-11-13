<template>
  <div>
      <span v-for="elem in thisProperty.elements" :key="elem.name">
        <input
          :type="switchType"
          :name="propertyId"
          :id="$id(propertyId + '.' + elem.name)"
          :value="elem.name"
          :disabled="thisProperty.state == 'Busy' ? 'disabled' : false"
          v-model="selectedSwitches"
          @change="sendSwitch(elem.name)"
        />
        <label :for="$id(propertyId + '.' + elem.name)">{{ elem.name }}</label>
      </span>
    </div>
</template>
<style scoped>
</style>
<script>
import indi from "~/mixins/indi.js";
export default {
  props: ["device", "property", "indiId"],
  mixins: [indi],
  methods: {
      sendSwitches: function (elemName) {
        this.sendIndiNew(
          this.thisDevice,
          this.thisProperty,
          elemName,
          'On'
        )
        console.log(`Setting ${elemName} On`)
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
    propertyId: function () {
      if (!(this.thisDevice && this.thisProperty)) return null;
      return this.thisDevice.name + '.' + this.thisProperty.name;
    },
    selectedSwitches: function () {
      if (!this.thisProperty) return {selectedSwitches: null};
      const enabledSwitches = Object.keys(this.thisProperty.elements).filter(
        key => this.thisProperty.elements[key].value == "On"
      );
      return this.switchType == "checkbox" ? enabledSwitches : enabledSwitches[0];
    }
  },
};
</script>
