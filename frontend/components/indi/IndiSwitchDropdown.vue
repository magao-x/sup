<template>
  <select :disabled="disabledOrMissing" @change="onChange" :value="selectedSwitch">
    <option
      v-for="elem in switchElements"
      :key="elem.name"
      :value="elem.name"
      :selected="elem.name == selectedSwitch"
    >{{ elem.label ? elem.label : elem.name }}</option>
  </select>
  <!-- <div>
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
  </div> -->
</template>
<style lang="scss" scoped>
</style>
<script>
import indi from "~/mixins/indi.js";
import ToggleButton from "~/components/basic/ToggleButton.vue";
import utils from "~/mixins/utils.js";

const noneSelected = "-none selected-";

export default {
  props: ["device", "property", "indiId", "disabled", "orientation", "allowNone"],
  mixins: [indi, utils],
  components: {
    ToggleButton
  },
  methods: {
    sendSwitch: function(element) {
      if (this.disabled) return;
      this.sendIndiNew(this.thisProperty, element, "On");
    },
    onChange: function(evt) {
      if (this.$el.value !== noneSelected) {
        this.sendSwitch(this.thisProperty._elements[this.$el.value]);
      } else {
        this.sendIndiNew(this.thisProperty, this.thisProperty._elements[this.selectedSwitch], "Off");
      }
    }
  },
  computed: {
    propertyId: function() {
      if (!(this.thisDevice && this.thisProperty)) return null;
      return this.thisDeviceName + "." + this.thisProperty.name;
    },
    switchElements: function () {
      if (!(this.thisDevice && this.thisProperty)) return null;
      let elements = Object.assign({}, this.thisProperty._elements);
      let defaultElement = {_value: "On", label: noneSelected, name: noneSelected};
      for (let el in elements) {
        if (elements[el]._value == 'On') {
          defaultElement._value = 'Off';
        }
      };
      if (this.allowNone) {
        elements[noneSelected] = defaultElement;
      }
      return elements;
    },
    selectedSwitch: function() {
      if (!this.thisProperty) return noneSelected;
      for (let el in this.switchElements) {
        if (this.switchElements[el]._value == 'On') {
          return el;
        }
      }
    },
    disabledOrMissing: function () {
      return this.disabled || !this.thisProperty || this.thisProperty.propertyState == 'Busy';
    }
  }
};
</script>
