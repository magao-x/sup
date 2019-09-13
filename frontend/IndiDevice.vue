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
@import './css/variables.scss';

.device {
  margin: 1rem;
  padding: 1rem;
  flex: 1;
}
</style>
<script>
import IndiProperty from "./IndiProperty.vue";
import utils from "./utils.js";

export default {
  props: ["device"],
  inject: ["time"],
  components: {
    IndiProperty
  },
  mixins: [utils]
};
</script>
