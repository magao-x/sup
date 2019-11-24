<template>
  <div class="adjustableNumberStepper">
    <input
      class="value"
      :value="value"
      :disabled="disabled"
      @input="$emit('input', $event.target.value)"
      @focus="$emit('focus')"
      @blur="$emit('blur')"
    />
    <div class="col" :class="{'disabled': disabled}">
      <div class="above" @click="crement(+1)">
        <button :disabled="disabled">+</button>
      </div>
      <div class="below" @click="crement(-1)">
        <button :disabled="disabled">-</button>
      </div>
      <div class="mid">
        <input v-model="stepInput" :disabled="disabled" />
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
.adjustableNumberStepper {
  input,
  button {
    // border: none;
    margin: 0;
    padding: 0;
  }
  width: 100%;
  display: flex;
  flex: 1;
  flex-direction: row;
  input.value {
    font: inherit;
    width: 100%;
    min-width: 6em;
    background-color: inherit;
    align-self: center;
  }
  .col.disabled {
    display: none;
  }
  .col {
    font-size: 0.666em;
    text-align: center;
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 0 0.125em;
    input {
      min-width: 4em;
      width: 100%;
      text-align: center;
      font: inherit;
      margin: 0;
      border: none;
      border-bottom: 1px solid;
      flex: 1;
      background: inherit;
    }
    .mid > input,
    .mid > .amount {
      padding: 0.5em;
      box-sizing: border-box;
      color: $primary;
    }
    .above {
      order: 1;
      button {
        border-radius: $round-radius $round-radius 0 0;
      }
    }
    .mid {
      order: 2;
    }
    .below {
      order: 3;
      button {
        border-radius: 0 0 $round-radius $round-radius;
      }
    }
  }
  button {
    font: inherit;
    flex: 1;
    width: 100%;
    min-width: 3em;
    padding: 0.25em;
    border: 1px solid $primary;
    background: inherit;
    color: $primary;
    font-weight: bold;
  }
  .above:hover > button,
  .above:hover ~ .mid {
    background-color: $primary;
    transition: background-color $transitionTime;
    color: $base03;
    input,
    .amount {
      color: $base03;
    }
  }
  .enabled.below:hover > button,
  .enabled.below:hover ~ .mid {
    background-color: $primary;
    transition: background-color $transitionTime;
    color: $base03;
    input,
    .amount {
      color: $base03;
    }
  }
  .amount {
    border-bottom: 1px solid transparent;
    width: 100%;
    display: inline-block;
  }
}
</style>
<script>
import utils from "~/mixins/utils.js";
export default {
  props: ["value", "min", "max", "step", "disabled", "format"],
  mixins: [utils],
  methods: {
    crement: function(signInt) {
      let newVal = Number(this.value) + signInt * Number(this.stepInput);
      if (!isNaN(newVal)) {
        if (typeof this.max !== "undefined") {
          if (newVal > this.max) {
            newVal = this.max;
          }
        }
        if (typeof this.min !== "undefined") {
          if (newVal < this.min) {
            newVal = this.min;
          }
        }
        if (this.format) {
          const [precision, type] = this.precisionFromFormat(this.format);
          if (!isNaN(precision)) {
            newVal = newVal.toFixed(precision);
          }
        }
        this.$emit("input", newVal);
      }
    },
    showCrement: function() {
      return this.step == 0 && this.disabled;
    }
  },
  watch: {
    step: function(newValue, oldValue) {
      this.stepInput = newValue;
    }
  },
  data: function() {
    return {
      stepInput: this.step
    };
  }
};
</script>