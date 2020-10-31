<template>
  <button class="square restore" :disabled="disabled" @click="$emit('sync')">
    <i class="material-icons">sync</i>
  </button>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
button.restore {
  border-bottom: 1px solid $restore;
  &:enabled:hover, &:enabled:active {
    border: 1px solid $restore;
  }
}
</style>
<script>
export default {
  props: {
    disabled: Boolean
  }
};
</script>
