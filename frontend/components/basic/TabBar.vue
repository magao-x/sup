<template>
   <component :is="TabBar" v-if="TabBar"></component>
   <div v-else class="error"><span>Configuration 'layout' value '{{ $store.state.config.layout }}'' is invalid. Please update the config file.</span></div>
</template>
<style lang="scss" scoped>
@import "~/css/variables.scss";
.error {
  padding: 1em;
  color: $error;
}
</style>
<script>
import constants from "~/constants.js";
import { map } from '~/map.js'
import { defineAsyncComponent } from "vue";

export default {
  computed: {
    TabBar() {
      const layout = this.$store.state.config.layout;
      if (map[layout] && map[layout]['tabBar']) {
        return defineAsyncComponent(map[layout]['tabBar']);
      } else {
        return null;
      }
    }
  },  
  inject: ['toggleFlames'],
  provide() {
    return {
      toggleFlames: this.toggleFlames
    };
  },  
};
</script>