<template>
  <div class="toggle-and-commit">
    <div :class="switchClasses">
      <div class="label off" :class="currentValue ? '' : 'current'" v-if="labelOff">{{ labelOff }}</div>
      <div>
      <div class="toggle" :class="classes" @click.prevent="toggleOrPrompt">
        <div class="doodad">{{ symbol }}</div>
      </div>
      </div>
      <div class="label on" :class="currentValue ? 'current' : ''"  v-if="labelOn">{{ labelOn }}</div>
    </div>
    <commit-button v-if="prompt" :disabled="!waitingToCommit" @commit="toggle"></commit-button>
  </div>
</template>
<style lang="scss" scoped>
@use "sass:color";
@use "@/css/variables.scss" as *;
.toggle-and-commit {
  display: inline-flex;
  .switch {
    flex: 1;
    // display: grid;
    // &.has-off-label.has-on-label {
    //   grid-template-columns: 1fr 1fr 1fr;
    // }
    // &.has-off-label, &.has-on-label {
    //   grid-template-columns: 1fr 1fr;
    // }
    // grid-template-columns: 1fr;
    display: flex;
    text-align: center;
    .toggle {
      margin: 0 auto;
      flex: 0;
    }
    .label {
      color: $alternate-gray;
      flex: 1;
    }
    .label.on {
      text-align: left;
      margin-left: $medgap;
    }
    .label.off {
      text-align: right;
      margin-right: $medgap;
    }
    .label.current {
      color: inherit;
    }
  }
}
.toggle {
  position: relative;
  display: inline-block;
  vertical-align: middle;
  width: 3em;
  height: calc(1.5em + 2px);
  border-radius: 1em;
  border: 1px solid $plasma-blue;
  user-select: none;
  color: var(--fg-normal);
  .doodad {
    position: absolute;
    width: 1.5em;
    border-radius: 0.75em;
    height: 1.5em;
    left: 0;
    text-align: center;
    vertical-align: middle;
    line-height: 1.5;
    border-left: none;
  }
  &.disabled, &.readOnly {
    color: var(--fg-inactive);
    border: 1px solid var(--fg-inactive);
    .doodad {
      border: 1px solid var(--fg-inactive);
    }
  }
  &.inactive, &.readOnly {
    .doodad {
      border: 1px solid $plasma-blue;
      background: transparent;
    }
  }
  &.busy {
    .doodad {
      left: auto;
      right: auto;
      margin: 0 auto;
      position: relative;
    }
  }
  &.activating.readWrite {
    .doodad {
      background: transparent;
      border: 1px solid $plasma-blue;
    }
  }
  &.deactivating.readWrite {
    .doodad {
      background: color.adjust($plasma-blue, $lightness: -10%);
      border: 1px solid transparent;
    }
  }
  &.active {
    &.readWrite {
      box-shadow: 0 0 5px color.adjust($plasma-blue, $lightness: 15%);
    }
    .doodad {
      left: auto;
      right: 0;
      border: 1px solid $plasma-blue;
    }
    &.enabled.readWrite {
      .doodad {
        background:  color.adjust($plasma-blue, $lightness: +15%);
      }
    }
    &.disabled {
      .doodad {
        background: color.adjust($plasma-blue, $lightness: -15%);
      }
    }
  }
}
button.commit {
  &:enabled {
    box-shadow: 0px 0px 5px $plasma-blue;
  }
}
</style>
<script>
import CommitButton from "@/components/basic/CommitButton.vue";
export default {
  props: ["value", "busy", "disabled", "prompt", "labelOn", "labelOff", "readOnly"],
  components: {CommitButton},
  data: function () {
    return {
      waitingToCommit: false,
      targetState: null
    };
  },
  computed: {
    currentValue: function () {
      return this.targetState === null ? this.value : this.targetState;
    },
    busyOrWaiting: function () {
      return this.busy || this.waitingToCommit;
    },
    classes: function() {
      return {
        inactive: !this.value && !this.busyOrWaiting,
        active: this.value && !this.busyOrWaiting,
        activating: this.value && this.busyOrWaiting && !this.disabled,
        busy: this.busy,
        deactivating: !this.value && this.busyOrWaiting && !this.disabled,
        disabled: this.disabled,
        enabled: !this.disabled,
        readOnly: this.readOnly,
        readWrite: !this.readOnly,
      };
    },
    switchClasses: function() {
      let classes = ['switch'];
      if (this.labelOff) { classes.push('has-off-label'); };
      if (this.labelOn) { classes.push('has-on-label'); };
      return classes;
    },
    symbol: function () {
      if (this.classes.disabled) {
        return "X"
      } else if (this.classes.inactive || this.classes.activating) {
        return "O";
      } else if (this.classes.active || this.classes.deactivating) {
        return "|";
      }
    }
  },
  methods: {
    toggleOrPrompt: function () {
      if (this.disabled || this.readOnly) return;
      if (!this.prompt) return this.toggle();
      this.targetState = !this.currentValue;
      if (this.targetState == this.value) {
        this.waitingToCommit = false;
      } else {
        this.waitingToCommit = true;
      }
    },
    toggle: function() {
      if (!this.disabled && !this.readOnly) {
        this.$emit("input", !this.value);
      }
      this.waitingToCommit = false;
    }
  }
};
</script>
