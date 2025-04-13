<template>
  <div v-if="indiDefined">
    <div class="flex-row">
      <div style="min-width: 50%">
        <div>FPS: <indi-property :device="thisDevice" :property="thisDevice['fps']"></indi-property></div>
        <div>Mode: <indi-property :device="thisDevice" :property="thisDevice['mode']"></indi-property></div>
      </div>
      <div style="min-width: 50%">
        <div>EM protection: <indi-property :device="thisDevice" :property="thisDevice['emProtectionReset']"></indi-property></div>
      </div>
    </div>
  </div>
  <div v-else>
    Waiting for wavefront sensor
  </div>
</template>
<script>
import IndiProperty from "@/components/indi/IndiProperty.vue";
import IndiElement from "@/components/indi/IndiElement.vue";
import IndiValue from "@/components/indi/IndiValue.vue";
import indi from "@/mixins/indi.js";

export default {
  props: ["device", "indiId"],
  mixins: [indi],
  components: {
    IndiProperty,
    IndiElement,
    IndiValue
  }
}
</script>