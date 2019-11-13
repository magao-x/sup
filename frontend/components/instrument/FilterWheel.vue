<template>
<indi-switch-multi-element :device="thisDevice" :property="thisDevice.properties['filterName']" ></indi-switch-multi-element>
</template>
<style lang="scss" scoped>
</style>
<script>
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import indi from "~/mixins/indi.js";

export default {
  mixins: [indi],
  props: ["device", "indiId"],
  components: {
    IndiSwitchMultiElement
  }
};
</script>