<template>
  <div>
    <div class="buttons" :style="styleProperties">
      <toggle-button
        v-for="elem in switchElements" 
        :key="elem.name"
        :disabled="disabled"
        :label="elem.name"
        :value="elem._value == 'On'"
        :busy="thisProperty.state == 'Busy'"
        @input="sendSwitch(elem)"/>
    </div>
  </div>
</template>
<style lang="scss" scoped>
.buttons {
  // display: flex;
  display:grid;
  padding: 0;
  // &.vertical {
  //   grid-template-columns: 1fr;
  // }
}
</style>
<script>
import indi from "@/mixins/indi.js";
import ToggleButton from "@/components/basic/ToggleButton.vue";
import utils from "@/mixins/utils.js";

export default {
  props: {
    device: {
      type: Object,
    },
    property: {
      type: Object,
    },
    indiId: {
      type: String,
    },
    disabled: {
      type: Boolean,
      default: false
    },
    columns: {
      type: Number,
      default: 3,
    }
  },
  mixins: [indi, utils],
  components: {
    ToggleButton
  },
  methods: {
    sendSwitch: function(element) {
      if (this.disabled) return;
      if (element._value == 'Off') {
        this.sendIndiNew(this.thisProperty, element, "On");
      } else {
        this.sendIndiNew(this.thisProperty, element, "Off");
      }
    }
  },
  computed: {
    styleProperties() {
      let colBits = [];
      let cols;
      if (typeof this.columns !== "undefined") {
        cols = this.columns;
      } else {
        cols = Object.keys(this.thisProperty._elements).length;
      }
      for (let i = 0; i < cols; i++) {
        colBits.push("1fr");
      }
      return {"grid-template-columns": colBits.join(" ")}
    },
    switchType: function() {
      if (this.thisProperty.rule == "OneOfMany") {
        return "radio";
      } else {
        return "checkbox";
      }
    },
    propertyId: function() {
      if (!(this.thisDevice && this.thisProperty)) return null;
      return this.thisDeviceName + "." + this.thisProperty.name;
    },
    switchElements: function () {
      if (!(this.thisDevice && this.thisProperty)) return null;
      return this.thisProperty._elements;
    },
    selectedSwitches: function() {
      if (!this.thisProperty) return { selectedSwitches: null };
      const enabledSwitches = Object.keys(this.thisProperty._elements).filter(
        key => this.thisProperty._elements[key]._value == "On"
      );
      return this.switchType == "checkbox"
        ? enabledSwitches
        : enabledSwitches[0];
    }
  }
};
</script>
