<template>
  <div class="observability-plot-container">
    <div class="plot-and-title altitude">
      <div class="plot-title">altitude: <indi-value class="value" :indi-id="`tcsi.telpos.el`" :format-function="(v) => applyFormatString('%1.4fº', v)"></indi-value></div>
      <plot-component v-if="altitudes !== null" :data="altitudePlotData" :timeSeries="true" :showNowUTC="true"
        :fixedYDomain="[0, 90]" :fixedYTicks="[0, 30, 45, 60, 90]" :legend="false"
        class="observability-plot"></plot-component>
      <div class="totals-grid">
        <div class="label">Obs</div>
        <div class="value">{{ observationTimeTotal }}</div>
        <div class="label">Target</div>
        <div class="value">{{ targetTimeTotal }}</div>
      </div>
    </div>
    <div class="plot-and-title parang">
      <div class="plot-title">parallactic angle: <indi-value class="value" :indi-id="`tcsi.teldata.pa`" :format-function="(v) => applyFormatString('%1.4fº', v)"></indi-value></div>
      <plot-component v-if="parallactic_angles !== null" :data="parallacticAnglePlotData" :timeSeries="true"
      :showNowUTC="true" :fixedYDomain="[-180, 180]" :fixedYTicks="[-180, -90, 0, 90, 180]" :legend="false"
      class="observability-plot"></plot-component>
      <div class="totals-grid">
        <div class="label">Obs</div>
        <div class="value">{{ observationDeltaParang }}º</div>
        <div class="label">Target</div>
        <div class="value">{{ targetDeltaParang }}º</div>
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.value {
  color: var(--fg-active);
}

.observability-plot-container {
  display: grid;
  grid-template-columns: subgrid;
  grid-template-rows: subgrid;
  // grid-gap: $unit;
  min-height: 150px;
  max-height: 337px;
  // flex: 1;

  // .grid {
  //   display: grid;
  //   grid-template-columns: 1fr 1fr 1fr 1fr;
  // }

  .plot-and-title {
    // display: flex;
    // flex-direction: column;
    // height: 100%;
    display: grid;
    grid-template-rows: subgrid;
    grid-template-columns: subgrid;
    .plot-title, .observability-plot {
      grid-column: 1/5;
    }
    .plot-title {
      grid-row: 1;
    }
    .observability-plot {
      grid-row: 2/4;
    }
    .grid-totals {
      grid-row: 5;
    }
    &.altitude {
      grid-column: 1/5;
      grid-row: 1/5;
    }
    &.parang {
      grid-column: 5/9;
      grid-row: 1/5;
    }
  }

  .observability-plot {
    height: 270px;
    padding-bottom: $medgap;
  }
}

.plot-title {
  padding: $medgap $unit;
  text-align: center;
  font-size: 150%;
}

.totals-grid {
  display: grid;
  grid-column: 1/5;
  // grid-template-columns: 1fr 1fr 1fr 1fr;
  grid-template-columns: subgrid;
  text-align: center;
  font-size: 150%;
  .label {
    text-align: right;
  }
  .value {
    text-align: left;
  }
}
.totals {
  min-width: 12em;

}
</style>
<script>
import PlotComponent from "@/components/plots/PlotComponent.vue";
import IndiValue from "@/components/indi/IndiValue.vue";
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";
import utils2 from "@/utils.js";

export default {
  props: ['equatorialCoords', 'beginObsTimestamp', 'observersDevice'],
  mixins: [indi, utils],
  inject: ["indi"],
  data: function () {
    return {
      parallactic_angles: null,
      altitudes: null,
    }
  },
  components: { PlotComponent, IndiValue },
  computed: {
    ra() {
      return this.equatorialCoords?.ra;
    },
    dec() {
      return this.equatorialCoords?.dec;
    },
    altitudePlotData() {
      return {
        "altitude": { points: this.altitudes, class: "glowy" },
        "moonrise": { vline: this.solar_system.moon.rise, dashed: true, color: "#4d4d4d" },
        "moonset": { vline: this.solar_system.moon.set, dashed: true, color: "#4d4d4d" },
        "sunrise": { vline: this.solar_system.sun.rise, dashed: true, color: "#fdbc4b" },
        "sunset": { vline: this.solar_system.sun.set, dashed: true, color: "#fdbc4b" },
      };
    },
    parallacticAnglePlotData() {
      let parangData = {
        "parallactic angle": { points: this.parallactic_angles, class: "glowy" },
      };
      let obsStart = this.retrieveValueByIndiId(`${this.observersDevice}.obs_start.observation`);
      let tgtStart = this.retrieveValueByIndiId(`${this.observersDevice}.obs_start.target`);
      if (obsStart) {
        parangData["obs start"] = { vspan: { from: obsStart, to: this.time.currentTime.toISO() }, dashed: true };
      }
      if (tgtStart) {
        parangData["tgt start"] = { vspan: { from: tgtStart, to: this.time.currentTime.toISO() }, dashed: true };
      }
      return parangData;
    },
    targetTimeTotal() {
      return this.formatSeconds(this.retrieveValueByIndiId(`${this.observersDevice}.obs_time.target`));
    },
    observationTimeTotal() {
      return this.formatSeconds(this.retrieveValueByIndiId(`${this.observersDevice}.obs_time.observation`));
    },
    targetDeltaParang() {
      return this.applyFormatString("%0.2f", this.retrieveValueByIndiId(`${this.observersDevice}.obs_delta_parang.target`));
    },
    observationDeltaParang() {
      return this.applyFormatString("%0.2f", this.retrieveValueByIndiId(`${this.observersDevice}.obs_delta_parang.observation`));
    },
  },
  methods: {
    async loadPlotData(ra, dec) {
      try {
        const destURL = utils2.buildBackendUrl(`airmass?ra=${ra}&dec=${dec}`);
        const res = await fetch(destURL);

        if (!res.ok) {
          const message = `An error has occured: ${res.status} - ${res.statusText}`;
          console.error(message);
          return { parallactic_angles: null, altitudes: null };
        }
        const data = await res.json();
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
