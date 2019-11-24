<template>
  <div class="dashboard">
    <loop-state indiId="aoloop"></loop-state>
    <div class="plot-panels">
      <indi-line-plot indiId="camacq.temp" style="height: 350px; flex:1"></indi-line-plot>
      <indi-line-plot indiId="camlowfs.temp_ccd" style="height: 350px;"></indi-line-plot>
      <indi-line-plot indiId="camsci1.temp_ccd" style="height: 350px;"></indi-line-plot>
      <indi-line-plot indiId="camsci2.temp_ccd" style="height: 350px;"></indi-line-plot>
      <indi-line-plot indiId="camwfs.temp_ccd" style="height: 350px;"></indi-line-plot>
    </div>
  </div>
</template>
<style lang="scss" scoped>
.dashboard {
  max-width: 100%;
}
.plot-panels {
  display: flex;
  flex-wrap: wrap;
  .plot-container {
    flex: 1;
  }
}
</style>
<script>
import VueLinePlot from "~/components/plots/VueLinePlot.vue";
import IndiLinePlot from "~/components/indi/IndiLinePlot.vue";
import LoopState from "~/components/instrument/LoopState.vue";

export default {
  components: {
    VueLinePlot,
    IndiLinePlot,
    LoopState
  }
};
</script>