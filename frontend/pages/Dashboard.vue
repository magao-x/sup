<template>
  <div class="dashboard">
    <loop-state indiId="aoloop"></loop-state>
    <div class="plot-panels">
      <indi-plot indiId="temprack.temperature" style="height: 350px;"></indi-plot>
      <indi-plot indiId="camacq.temp" style="height: 350px;"></indi-plot>
      <indi-plot indiId="camlowfs.temp_ccd" style="height: 350px;"></indi-plot>
      <indi-plot indiId="camsci1.temp_ccd" style="height: 350px;"></indi-plot>
      <indi-plot indiId="camsci2.temp_ccd" style="height: 350px;"></indi-plot>
      <indi-plot indiId="camwfs.temp_ccd" style="height: 350px;"></indi-plot>
      <indi-plot indiId="camwfs.temps.water" style="height: 350px;"></indi-plot>

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
  .plot {
    flex: 1;
  }
}
</style>
<script>
import IndiPlot from "~/components/indi/IndiPlot.vue";
import LoopState from "~/components/instrument/LoopState.vue";

export default {
  components: {
    IndiPlot,
    LoopState
  }
};
</script>