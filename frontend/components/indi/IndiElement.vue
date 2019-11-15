<template>
  <div v-if="thisElement" class="element">
    <sync-button v-if="propertyKind !== 'swt'" :disabled="isDisabled" @sync="onSync"></sync-button>
    <adjustable-number-stepper
      v-if="propertyKind == 'num'"
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
    <input
      v-else
      :disabled="isDisabled"
      :value="currentValueOrInput"
      @focus="stopUpdating"
      @blur="maybeResumeUpdating"
      @input="updateUserInput"
    >
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
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  props: ["device", "property", "element", "indiId"],
  components: {
    SyncButton,
    CommitButton,
    AdjustableNumberStepper,
    IndiToggleSwitch,
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
      if (payload.target.value) {
        this.userInput = payload.target.value;
      } else {
        this.userInput = payload;
      }
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
      console.log('sending', this.thisDevice.name,
        this.thisProperty.name,
        this.thisElement.name,
        this.userInput);
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
    theControl: function() {
      if (!this.thisProperty) return;
      if(this.thisProperty.kind == 'swt') {
        return IndiToggleSwitch;
      } else if (this.thisProperty.kind == 'num') {
        return IndiAdjustableNumberStepper;
      } else {
        return IndiText;
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
      // console.log('computing currentValue...');
      if (this.thisElement) {
        // console.log('have it');
        return this.thisElement.value;
      } else {
        // console.log('dont have it');
        return "";
      }
    },
    currentValueOrInput: function () {
      if (this.userInput !== null) {
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
