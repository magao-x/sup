<template>
  <div class="dashboard">

    <div class="plot-panels">
      <indi-plot indiId="temprack.temperature" ></indi-plot>
      <indi-plot indiId="camacq.temp" ></indi-plot>
      <indi-plot indiId="camsci1.temp_ccd" ></indi-plot>
      <indi-plot indiId="camsci2.temp_ccd" ></indi-plot>
      <indi-plot indiId="camwfs.temp_ccd" ></indi-plot>
      <indi-plot indiId="camwfs.temps.water" ></indi-plot>
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
    min-width: 350px;
    max-width: 100%;
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