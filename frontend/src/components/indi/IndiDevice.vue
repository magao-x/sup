<template>
  <div v-if="thisDevice" class="device">
    <indi-property
      v-for="prop in thisDevice"
      :key="thisDeviceName + '.' + prop.name"
      :device="thisDevice"
      :property="prop"
    ></indi-property>
  </div>
  <div v-else>Waiting for device</div>
</template>
<style lang="scss" scoped>
@use '@/css/variables.scss' as *;

.device {
  margin: 1rem;
  padding: 1rem;
  flex: 1;
}
</style>
<script>
import IndiProperty from "./IndiProperty.vue";
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";

export default {
  props: ["device", "indiId"],
  inject: ["indi"],
  components: {
    IndiProperty
  },
  mixins: [indi, utils]
};
</script>
