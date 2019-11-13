<template>
  <div class="toggle" :class="classes" @click.prevent="toggle">
    <div class="doodad">{{ value ? "I" : "O" }}</div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
.toggle {
  position: relative;
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
  &.active {
    box-shadow: 0 0 5px lighten($primary, 15);
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
export default {
  props: ["value", "busy"],
  computed: {
    classes: function() {
      return {
        inactive: !this.value && !this.busy,
        active: this.value && !this.busy,
        activating: this.value && this.busy,
        deactivating: !this.value && this.busy
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
    toggle: function() {
      this.$emit("input", !this.value);
    }
  }
};
</script>