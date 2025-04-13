<template>
  <div><div>ADC speed:</div><indi-switch-multi-element :device="thisDevice" :property="adcSpeedProperty"></indi-switch-multi-element></div>
</template>
<style lang="scss" scoped>

</style>
<script>
import indi from "@/mixins/indi.js";
import IndiSwitchMultiElement from "@/components/indi/IndiSwitchMultiElement.vue";

export default {
    props: ["device", "indiId"],
    mixins: [indi],
    components: {
      IndiSwitchMultiElement,
    },
    computed: {
      adcSpeedProperty() {
        if (!this.thisDevice) return null;
        return this.thisDevice['adcspeed'];
      }
    }
}
</script>