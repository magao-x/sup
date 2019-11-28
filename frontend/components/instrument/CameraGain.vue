<template>
  <indi-property :device="thisDevice" :property="emgain"></indi-property>
</template>
<style lang="scss" scoped>
</style>
<script>
import indi from "~/mixins/indi.js";
import IndiProperty from "~/components/indi/IndiProperty.vue";

export default {
  props: ["device", "indiId"],
  mixins: [indi],
  components: {
    IndiProperty
  },
  computed: {
    emgain() {
      if (!this.thisDevice) return null;
      return this.thisDevice.properties.emgain;
    }
  }
};
</script>