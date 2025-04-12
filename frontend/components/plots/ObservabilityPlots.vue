<template>
  <div class="observability-plot-container">
    <div class="plot-and-title">
      <div class="plot-title">altitude</div>
      <plot-component
        v-if="altitudes !== null"
        :data="altitudePlotData"
        :timeSeries="true"
        :showNowUTC="true"
        :fixedYDomain="[0, 90]"
        :fixedYTicks="[0, 30, 45, 60, 90]"
        :legend="false"
        class="observability-plot"
      ></plot-component>
    </div>
    <div class="plot-and-title">
      <div class="plot-title">parallactic angle</div>
      <plot-component
        v-if="parallactic_angles !== null"
        :data="parallacticAnglePlotData"
        :timeSeries="true"
        :showNowUTC="true"
        :fixedYDomain="[-180, 180]"
        :fixedYTicks="[-180, -90, 0, 90, 180]"
        :legend="false"
        class="observability-plot"
      ></plot-component>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@use "./css/variables.scss" as *;

.observability-plot-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-gap: $unit;
  min-height: 150px;
  max-height: 337px;
  .plot-and-title {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  .observability-plot {
    flex: 1;
    padding-bottom: $medgap;
  }
}
.plot-title {
  color: $plasma-blue;
  padding: $medgap $unit;
  text-align: center;
}
</style>
<script>
import PlotComponent from "~/components/plots/PlotComponent.vue";
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import utils2 from "~/utils.js";

export default {
  props: ['equatorialCoords', 'beginObsTimestamp'],
  mixins: [indi, utils],
  inject: ["indi"],
  data: function () {
    return {
      parallactic_angles: null,
      altitudes: null,
    }
  },
  components: { PlotComponent },
  computed: {
    ra() {
      return this.equatorialCoords?.ra;
    },
    dec() {
      return this.equatorialCoords?.dec;
    },
    altitudePlotData() {
      return {
        "altitude": {points: this.altitudes}, 
        "moonrise": {vline: this.solar_system.moon.rise, dashed: true, color: "#4d4d4d"},
        "moonset": {vline: this.solar_system.moon.set, dashed: true, color: "#4d4d4d"},
        "sunrise": {vline: this.solar_system.sun.rise, dashed: true, color: "#fdbc4b"},
        "sunset": {vline: this.solar_system.sun.set, dashed: true, color: "#fdbc4b"},
    };
    },
    parallacticAnglePlotData() {
      let parangData = {
        "parallactic angle": {points: this.parallactic_angles},
      };
      let obsStart = this.retrieveValueByIndiId(`observers.obs_start.observation`);
      let tgtStart = this.retrieveValueByIndiId(`observers.obs_start.target`);
      if (obsStart) {
        console.log(obsStart);
        parangData["obs start"] = {vspan: {from: obsStart, to: this.time.currentTime.toISO()}, dashed: true};
      }
      if (tgtStart) {
        console.log(tgtStart);
        parangData["tgt start"] = {vspan: {from: tgtStart, to: this.time.currentTime.toISO()}, dashed: true};
      }
      return parangData;
    },
  },
  methods: {
    async loadPlotData(ra, dec) {
      try {
        const destURL = utils2.buildBackendUrl(`airmass?ra=${ra}&dec=${dec}`);
        const res = await fetch(destURL);
        console.log("Fetched result");
        
        if (!res.ok) {
          console.log("not ok");
          const message = `An error has occured: ${res.status} - ${res.statusText}`;
          console.error(message);
          return {parallactic_angles: null, altitudes: null};
        }
        const data = await res.json();
        console.log(data);
        return data;
      } catch (err) {
        console.error("Error in retrieving altitude/parang:", err);
      }
    },
    async setPlotData(data) {
      console.log("Setting plot data on component");
      this.parallactic_angles = data.parallactic_angles;
      this.altitudes = data.altitudes;
      this.solar_system = data.solar_system;
      console.log("Done setting plot data");
    }
  },
  async mounted() {
    if (this.ra == null || this.dec == null) return;
    console.log("loading plot data from mounted");
    const data = await this.loadPlotData(this.ra, this.dec);
    console.log("Loaded plot data after mount");
    await this.setPlotData(data);
  },
  watch: {
    async equatorialCoords(newCoords, oldCoords) {
      if (newCoords && newCoords.ra && newCoords.dec
      //  && (oldCoords.ra !== newCoords.ra || oldCoords.dec !== newCoords.dec)
      ) {
        let data = await this.loadPlotData(newCoords.ra, newCoords.dec);
        if (!data) {
          return;
        }
        await this.setPlotData(data);
        console.log("updated plot");
      }
    }
  }
};
</script>

