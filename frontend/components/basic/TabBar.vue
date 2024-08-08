<template>
  <TabBarScoob v-if="$store.state.config.layout === 'SCOOB'"></TabBarScoob>
  <TabBarMagAOX v-else-if="$store.state.config.layout === 'MAGAOX'"></TabBarMagAOX>
  <TabBarMagAOX v-else></TabBarMagAOX>
</template>
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