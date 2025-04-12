<template>
  <div class="status-indicator" :class="state">
    {{ label }}
    <span v-if="iconOk && state == 'ok'" class="material-icons" >{{ iconOk }}</span>
    <span v-else-if="iconAlert" class="material-icons" >{{ iconAlert }}</span>
  </div>
</template>
<style lang="scss" scoped>
@use '~/css/variables.scss' as *;

.material-icons {
  // font-size: calc(0.75 * 24px);
  line-height: 0;
  font-size: 1rem;
  margin: 0;
  margin-bottom: 0.1rem;
  vertical-align: middle;
}

.alert {
  background-color: $warning;
  border-color: darken($icon-orange, 15);
}
</style>
<script>
export default {
  props: ["state", "label", "icon-ok", "icon-alert"],
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
