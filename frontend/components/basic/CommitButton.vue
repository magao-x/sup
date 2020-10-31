<template>
  <button class="square commit" :disabled="disabled" @click="$emit('commit')"><i class="material-icons">done</i></button>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
button.commit {
  border-bottom: 1px solid $commit;
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
