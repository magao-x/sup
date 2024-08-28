<template>
  <div class="dashboard cols">
    <div class="plot-panels col">
      <indi-plot indiId="temprack.temperature" ></indi-plot>
      <indi-plot indiId="camacq.temp" ></indi-plot>
      <indi-plot indiId="camsci1.temp_ccd" ></indi-plot>
      <indi-plot indiId="camsci2.temp_ccd" ></indi-plot>
      <indi-plot indiId="camwfs.temp_ccd" ></indi-plot>
      <indi-plot indiId="camwfs.temps.water" ></indi-plot>
    </div>
    <zoomed-iframe class="col" id="lco-weather" src="http://weather.lco.cl/" :width="1855"></zoomed-iframe>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
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
#lco-weather {
  padding: $unit;
}
</style>
<script>
import IndiPlot from "~/components/indi/IndiPlot.vue";
import LoopState from "~/components/instrument/LoopState.vue";
import ZoomedIframe from "~/components/basic/ZoomedIframe.vue";

export default {
  components: {
    IndiPlot,
    LoopState,
    ZoomedIframe
  }
};
</script>