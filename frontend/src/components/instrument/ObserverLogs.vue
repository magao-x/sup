<template>
  <div v-if="retrieveByIndiId('observers')">
    <indi-element indi-id="observers.user_log.message" class="full-width"></indi-element>
  </div>
  <div v-else>
    Waiting for observers device...
  </div>
</template>
<script>
import utils from "@/mixins/utils.js";
import IndiElement from "@/components/indi/IndiElement.vue";
export default {
  mixins: [utils],
  inject: ["indi"],
  components: {
    IndiElement,
  },
}
</script>