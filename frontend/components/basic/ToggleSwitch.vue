<template>
  <div class="toggle-and-commit">
  <div class="toggle" :class="classes" @click.prevent="toggleOrPrompt">
    <div class="doodad">{{ currentValue ? "|" : "O" }}</div>
  </div>
  <commit-button v-if="prompt" :disabled="!waitingToCommit" @commit="toggle"></commit-button>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
.toggle-and-commit {
  display: inline-block;
  vertical-align: middle;
  margin-bottom: 3px;
  height: 2em;
}
.toggle {
  position: relative;
  display: inline-block;
  vertical-align: middle;
  width: 3em;
  height: calc(1.5em + 2px);
  border-radius: 1em;
  border: 1px solid $primary;
  user-select: none;
  color: $base3;
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
  &.inactive {
    .doodad {
      border: 1px solid $primary;
      background: transparent;
    }
  }
  &.activating {
    .doodad {
      left: auto;
      right: auto;
      margin: 0 auto;
      position: relative;
      background: transparent;
      border: 1px solid $primary;
    }
  }
  &.deactivating {
    .doodad {
      left: auto;
      right: auto;
      margin: 0 auto;
      position: relative;
      background: darken($primary, 10);
      border: 1px solid transparent;
    }
  }
  &.active.enabled {
    // box-shadow: 0 0 5px lighten($primary, 15);
    .doodad {
      left: auto;
      right: 0;
      background:  lighten($primary, 15);
      border: 1px solid $primary;
    }
  }
}
</style>
<script>
import CommitButton from "~/components/basic/CommitButton.vue";
export default {
  props: ["value", "busy", "disabled", "prompt"],
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
        activating: this.value && this.busyOrWaiting,
        deactivating: !this.value && this.busyOrWaiting,
        disabled: this.disabled,
        enabled: !this.disabled
      };
    },
    symbol: function () {
      if (this.classes.inactive || this.classes.activating) {
        return "O";
      } else if (this.classes.active || this.classes.deactivating) {
        return "I";
      }
    }
  },
  methods: {
    toggleOrPrompt: function () {
      if (this.disabled) return;
      if (!this.prompt) return this.toggle();
      this.targetState = !this.currentValue;
      if (this.targetState == this.value) {
        this.waitingToCommit = false;
      } else {
        this.waitingToCommit = true;
      }
    },
    toggle: function() {
      if (!this.disabled) {
        this.$emit("input", !this.value);
      }
      this.waitingToCommit = false;
    }
  }
};
</script>