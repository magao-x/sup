<template>
  <div>
    <div>Exposure time:</div>
    <indi-property :device="thisDevice" :property="exptime" style="font-size: 1.2em;"></indi-property>
  </div>
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
    exptime() {
      if (!this.thisDevice) return null;
      return this.thisDevice.properties.exptime;
    }
  }
};
</script>