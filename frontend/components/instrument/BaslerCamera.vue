<template>
  <div class="basler-camera" v-if="indiDefined">
    <div>{{ thisDeviceName }}</div>
    <p>Exposure time:</p>
    <indi-property :device="thisDevice" :property="thisDevice['exptime']"></indi-property>
  </div>
  <div class="basler-camera" v-else>
    Waiting for Basler camera...
  </div>
</template>
<style lang="scss" scoped>
.basler-camera {
  margin: 1rem;
  flex: 1;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiProperty from "~/components/indi/IndiProperty.vue";

export default {
  mixins: [indi, utils],
  props: ["device", "indiId", "disabled"],
  components: {
    IndiProperty,
  }
}
</script>