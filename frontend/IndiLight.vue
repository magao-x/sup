<template>
  <div class="light" :class="state">
    {{ state }}
  </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';

.light {
  border: 1px solid;
  line-height: 1.0;
  padding: 0.3 * $unit 0.6 * $unit;
  display: inline-block;
  color: $base03;
}
.Alert {
  background-color: $orange;
  border-color: darken($orange, 15);
}
.Ok {
  background-color: $green;
  border-color: darken($green, 15);
}
.Busy {
  color: $base2;
}
.Idle {
    color: $base1;
}
</style>
<script>

export default {
  props: ["state"]
}
</script>
