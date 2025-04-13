<template>
  <button class="square cancel" :disabled="disabled" @click="$emit('cancel')"><i class="material-icons">block</i></button>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;
button.cancel {
  border-bottom: 1px solid $warning;
  font-weight: bold;
  &:enabled {
    background: var(--btn-warn-bg-gradient);
  }
  &:enabled:hover, &:enabled:active {
    border: 1px solid $warning;
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
