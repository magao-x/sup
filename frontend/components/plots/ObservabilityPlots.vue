<template>
  <div class="observability-plot-container gap-bottom">
    <div class="view">
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
    <div class="view">
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
@import "./css/variables.scss";

.observability-plot-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-gap: $unit;
}
.plot-title {
  color: $plasma-blue;
  padding: $medgap $unit;
  text-align: center;
}
</style>
<script>
import PlotComponent from "~/components/plots/PlotComponent.vue";

export default {
  props: ['equatorialCoords'],
  data: function () {
    return {
      parallactic_angles: null,
      altitudes: null,
    }
  },
  components: { PlotComponent },
  computed: {
    ra() {
      return this.equatorialCoords.ra;
    },
    dec() {
      return this.equatorialCoords.dec;
    },
    altitudePlotData() {
      return {"altitude": {points: this.altitudes}};
    },
    parallacticAnglePlotData() {
      return {"parallactic angle": {points: this.parallactic_angles}}
    },
  },
  methods: {
    async loadPlotData() {
      try {
        let baseURL;
        if (process.env.NODE_ENV == 'development') {
          baseURL = "https://exao1.magao-x.org:4434"
        } else {
          baseURL =
            window.location.protocol +
            "//" +
            window.location.hostname +
            ":" +
            String(window.location.port);
        }
        const res = await fetch(`${baseURL}/airmass?ra=${this.ra}&dec=${this.dec}`);
        if (!res.ok) {
          const message = `An error has occured: ${res.status} - ${res.statusText}`;
          throw new Error(message);
        }
        const data = await res.json();
        this.parallactic_angles = data.parallactic_angles;
        this.altitudes = data.altitudes;
      } catch (err) {
        this.parallactic_angles = null;
        this.altitudes = null;
      }
    },
  },
  async mounted() {
    if (this.ra == null || this.dec == null) return;
    await this.loadPlotData();
  },
  watch: {
    async equatorialCoords(oldCoords, newCoords) {
      if (newCoords && (oldCoords.ra !== newCoords.ra || oldCoords.dec !== newCoords.dec)) {
        console.log("loading plot data from watcher");
        await this.loadPlotData();
      }
    }
  }
};
</script>

