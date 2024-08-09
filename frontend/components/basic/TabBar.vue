<template>
  <TabBarScoob v-if="$store.state.config.layout === 'SCOOB'"></TabBarScoob>
  <TabBarMagAOX v-else-if="$store.state.config.layout === 'MAGAOX'"></TabBarMagAOX>
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
import TabBarMagAOX from "~/pages/MagAOX/TabBar.vue";
import TabBarScoob from "~/pages/Scoob/TabBar.vue";

export default {
  components: {
    TabBarMagAOX,
    TabBarScoob,
  },
  inject: ['toggleFlames'],
  provide() {
    return {
      toggleFlames: this.toggleFlames
    };
  },  
};
</script>