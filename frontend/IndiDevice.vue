<template>
  <div class="device">
    <indi-property
      v-for="prop in objectAsSortedArray(device.properties)"
      :key="device.name + '.' + prop.name"
      :device="device"
      :property="prop"
    ></indi-property>
  </div>
</template>
<style lang="scss" scoped>
.device {
  border: 1px solid #ee6f31;
  padding: 1rem;
}
</style>
<script>
import IndiProperty from "./IndiProperty.vue";
import utils from "./utils.js";

export default {
  props: ["device"],
  components: {
    IndiProperty
  },
  mixins: [utils]
};
</script>
