<template>
  <button class="square edit" :disabled="disabled" @click="$emit('edit')"><i class="material-icons">edit</i></button>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
button.edit {
  border-bottom: 1px solid $kumquat;
  font-weight: bold;
  &:enabled {
    background: var(--btn-edit-bg-gradient);
  }
  &:enabled:hover, &:enabled:active {
    border: 1px solid $kumquat;
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
