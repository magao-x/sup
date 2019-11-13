<template>
  <button class="square commit" :disabled="disabled" @click="$emit('commit')"><i class="material-icons">done</i></button>
</template>
<style lang="scss" scoped>
</style>
<script>
export default {
  props: {
    disabled: Boolean
  }
};
</script>