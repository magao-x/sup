<template>
  <button class="square commit" :disabled="disabled" @click="$emit('commit')"><i class="material-icons">done</i></button>
</template>
<style lang="scss" scoped>
@use "./css/variables.scss" as *;
button.commit {
  border-bottom: 1px solid $commit;
  font-weight: bold;
  &:enabled {
    background: var(--btn-commit-bg-gradient);
  }
  &:enabled:hover, &:enabled:active {
    border: 1px solid $commit;
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
