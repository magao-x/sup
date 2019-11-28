<template>
  <div>
    <div>Frames per second:</div>
    <indi-property :device="thisDevice" :property="fps"></indi-property>
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
    fps() {
      if (!this.thisDevice) return null;
      return this.thisDevice.properties.fps;
    }
  }
};
</script>