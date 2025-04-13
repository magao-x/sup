<template>
  <div class="toggle btn" :class="classes" @click.prevent="toggle">
    {{ label }}
  </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss";
@use "@/css/main.scss";
.toggle.btn {
  &.inactive {}
  &.active {}
  &.activating {}
  &.deactivating {}
}
</style>
<script>
export default {
  props: ["value", "busy", "label", "disabled"],
  computed: {
    classes: function() {
      return {
        inactive: !this.value && !this.busy,
        active: this.value && !this.busy,
        activating: this.value && this.busy,
        deactivating: !this.value && this.busy,
        disabled: this.disabled,
        enabled: !this.disabled
      };
    }
  },
  methods: {
    toggle: function() {
      this.$emit("input", !this.value);
    }
  }
};
</script>