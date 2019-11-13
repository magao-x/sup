<template>
  <button class="square restore" :disabled="disabled" @click="$emit('sync')">
    <i class="material-icons">sync</i>
  </button>
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