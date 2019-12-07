<template>
  <div v-if="thisElement" class="element">
    <sync-button v-if="propertyKind !== 'swt'" :disabled="isDisabled" @sync="onSync"></sync-button>
    <adjustable-number-stepper
      v-if="propertyKind == 'num' && optionalAttr('step')"
      :disabled="isDisabled"
      :min="optionalAttr('min')"
      :max="optionalAttr('max')"
      :step="optionalAttr('step')"
      :format="optionalAttr('format')"
      :value="currentValueOrInput"
      @focus="stopUpdating"
      @blur="maybeResumeUpdating"
      @input="updateUserInput"
    ></adjustable-number-stepper>
    <indi-toggle-switch
      v-else-if="propertyKind == 'swt'"
      :disabled="isDisabled"
      :value="currentValueOrInput"
      :device="thisDevice"
      :property="thisProperty"
      :element="thisElement"
    ></indi-toggle-switch>
    <vanilla-input
      v-else
      :disabled="isDisabled"
      :value="currentValueOrInput"
      @focus="stopUpdating"
      @blur="maybeResumeUpdating"
      @input="updateUserInput"
    ></vanilla-input>
    <commit-button v-if="propertyKind !== 'swt'" :disabled="isDisabled" @commit="onCommit"></commit-button>
  </div>
  <div v-else>Waiting for element {{ indiId }}  {{ thisElement }}</div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

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
import SyncButton from "~/components/basic/SyncButton.vue";
import CommitButton from "~/components/basic/CommitButton.vue";
import AdjustableNumberStepper from "~/components/basic/AdjustableNumberStepper.vue";
// import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import IndiToggleSwitch from "~/components/indi/IndiToggleSwitch.vue";
import VanillaInput from "~/components/basic/VanillaInput.vue";
import VanillaNumberInput from "~/components/basic/VanillaNumberInput.vue";
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  props: ["device", "property", "element", "indiId"],
  components: {
    SyncButton,
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
    maybeResumeUpdating: function() {
      if (!this.isModified) {
        this.shouldUpdate = true;
      }
    },
    updateUserInput: function (payload) {
      this.userInput = payload;
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
    onSync: function() {
      this.userInput = this.currentValue;
      this.shouldUpdate = true;
    },
    onCommit: function () {
      this.sendIndiNew(
        this.thisDevice,
        this.thisProperty,
        this.thisElement,
        this.userInput
      );
      this.shouldUpdate = true;
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
        return this.thisProperty.kind;
      } else {
        return null;
      }
    },
    dottedName: function() {
      return (
        this.thisDevice.name + "." + this.thisProperty.name + "." + this.thisElement.name
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
        return this.thisElement.value;
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
        this.thisProperty.elements.hasOwnProperty("target")
      ) {
        return true;
      }
      return false;
    },
    isDisabled: function() {
      return (
        this.element === null ||
        this.thisProperty.perm === "ro" ||
        this.isPairedCurrent
      );
    }
  }
};
</script>
