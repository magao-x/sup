<template>
  <div class="light" :class="state">
    {{ labelOrState }}
  </div>
</template>
<style lang="scss" scoped>
@use 'sass:color';
@use '@/css/variables.scss' as *;

.light {
  border: 1px solid;
  line-height: 1.0;
  padding: 0.3 * $unit 0.6 * $unit;
  display: inline-block;
  color: var(--inset-bg);
}
.Alert {
  background-color: $warning;
  border-color: color.adjust($icon-orange, $lightness: -15%);
}
.Ok {
  background-color: $ok;
  border-color: color.adjust($ok, $lightness: -15%);
}
.Busy {
  color: var(--fg-visited);
}
.Idle {
    color: var(--fg-normal);
}
</style>
<script>

export default {
  props: ["state", "label"],
  computed: {
    labelOrState: function() {
      if (typeof this.label === "undefined") {
        return this.state;
      } else {
        return this.label;
      }
    }
  }
}
</script>
