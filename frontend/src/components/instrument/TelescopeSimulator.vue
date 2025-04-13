<template>
  <div>
    <div style="font-size: 2em;">Source power: <power-toggle indi-id="pdu0.source" :confirm="true"></power-toggle></div>
    <motion-stage kind="filterwheel" indi-id="fwtelsim"></motion-stage>
    <motion-stage kind="stage" indi-id="stagepickoff"></motion-stage>
  </div>
</template>
<style lang="scss" scoped>
</style>
<script>
import MotionStage from "@/components/instrument/MotionStage.vue";
import PowerToggle from "@/components/instrument/PowerToggle.vue";
import indi from "@/mixins/indi.js";

export default {
  props: ["device", "indiId"],
  components: {
    PowerToggle,
    MotionStage
  }
};
</script>