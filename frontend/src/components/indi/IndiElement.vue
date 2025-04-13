<template>
  <div v-if="thisElement" class="element">
    <indi-toggle-switch
      v-if="propertyKind == 'swt'"
      :disabled="isDisabled"
      :value="currentValueOrInput"
      :device="thisDevice"
      :property="thisProperty"
      :element="thisElement"
    ></indi-toggle-switch>
    <input
      v-else
      :disabled="isDisabled"
      :value="currentValueOrInput"
      @focus="stopUpdating"
      @input="updateUserInput"
      @keydown.enter="onCommit"
      @keydown.escape="cancel"
    ></input>
    <commit-button v-if="propertyKind !== 'swt' && !forceDisabled" :disabled="isDisabled" @commit="onCommit"></commit-button>
  </div>
  <div v-else>Waiting for element {{ indiId }}  {{ thisElement }}</div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.element {
  display: flex;
}
input {
  flex: 1;
  width: $unit;
  min-width: $unit;
}
</style>
<script>
import CommitButton from "@/components/basic/CommitButton.vue";
import AdjustableNumberStepper from "@/components/basic/AdjustableNumberStepper.vue";
// import ToggleSwitch from "@/components/basic/ToggleSwitch.vue";
import IndiToggleSwitch from "@/components/indi/IndiToggleSwitch.vue";
import VanillaInput from "@/components/basic/VanillaInput.vue";
import VanillaNumberInput from "@/components/basic/VanillaNumberInput.vue";
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";

export default {
  props: ["device", "property", "element", "indiId", "forceDisabled"],
  components: {
    CommitButton,
    AdjustableNumberStepper,
    IndiToggleSwitch,
    VanillaInput,
    VanillaNumberInput
  },
  mixins: [indi, utils],
  methods: {
    stopUpdating: function() {
      this.shouldUpdate = false;
    },
    cancel: function() {
      this.shouldUpdate = true;
      this.userInput = null;
    },
    updateUserInput: function (payload) {
      this.userInput = payload.target.value;
      this.isModified = true;
      this.shouldUpdate = false;
    },
    optionalAttr: function(attr) {
      if (this.thisElement && this.thisElement.hasOwnProperty(attr)) {
        return this.thisElement[attr];
      } else {
        return null;
      }
    },
    onCommit: function () {
      this.sendIndiNew(
        this.thisProperty,
        this.thisElement,
        this.currentValueOrInput
      );
      this.shouldUpdate = true;
      this.$emit('commit');
    }
  },
  data: function() {
    return {
      userInput: null,
      shouldUpdate: true,
      isModified: false
    };
  },
  computed: {
    propertyKind: function () {
      if(this.thisProperty) {
        return this.thisProperty._kind;
      } else {
        return null;
      }
    },
    dottedName: function() {
      return (
        this.thisDeviceName + "." + this.thisProperty.name + "." + this.thisElement.name
      );
    },
    displayName: function() {
      if (this.thisElement.label !== null) {
        return this.thisElement.label;
      } else {
        return this.dottedName;
      }
    },
    currentValue: function() {
      if (this.thisElement) {
        return this.thisElement._value;
      } else {
        return "";
      }
    },
    currentValueOrInput: function () {
      if (this.shouldUpdate === false && this.userInput !== null) {
        return this.userInput;
      } else {
        if (this.propertyKind == 'num' && this.thisElement.format) {
          return this.applyFormatString(this.thisElement.format, this.currentValue);
        } else {
          return this.currentValue;
        }
      }
    },
    isPairedCurrent: function() {
      if (
        this.element &&
        this.element.name === "current" &&
        this.thisProperty._elements.hasOwnProperty("target")
      ) {
        return true;
      }
      return false;
    },
    isDisabled: function() {
      return (
        this.forceDisabled === true ||
        this.element === null ||
        this.thisProperty.perm === "ro" ||
        this.isPairedCurrent
      );
    }
  }
};
</script>
