<template>
  <div>
    Gain: <indi-property :device="thisDevice" :property="emgain"></indi-property>
  </div>
</template>
<style lang="scss" scoped>
</style>
<script>
import indi from "@/mixins/indi.js";
import IndiProperty from "@/components/indi/IndiProperty.vue";

export default {
  props: ["device", "indiId"],
  mixins: [indi],
  components: {
    IndiProperty
  },
  computed: {
    emgain() {
      if (!this.thisDevice) return null;
      return this.thisDevice.emgain;
    }
  }
};
</script>