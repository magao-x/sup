<template>
    <indi-toggle-switch
      v-if="thisDevice"
      class="stream-writer-toggle"
      :prompt="true"
      :indi-id="thisDevice.name + '.writing.toggle'"
      labelOn="WRITING"
      labelOff="PAUSED"
    ></indi-toggle-switch>
    <div v-else>Waiting for streamwriter</div>
</template>
<style lang="scss" scoped>
.stream-writer-toggle {
  max-width: 18em;
}
</style>
<script>
import IndiToggleSwitch from "~/components/indi/IndiToggleSwitch.vue";
import indi from "~/mixins/indi.js";

export default {
  props: ["device", "indiId"],
  mixins: [indi],
  components: {
    IndiToggleSwitch
  }
}
</script>