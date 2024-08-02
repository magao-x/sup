<template>
  <TabBarScoob v-if="showScoob"></TabBarScoob>
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
  computed: {
    showScoob: function () {
      console.log("Should I show Scoob?")
      return this.config.layout === constants.SCOOB;
    },    
  },
  inject: ['toggleFlames', 'config'],
  provide() {
    return {
      toggleFlames: this.toggleFlames
    };
  },  
};
</script>