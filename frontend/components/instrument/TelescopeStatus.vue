<template>
  <div class="telescope-status" v-if="connected">
      <div class="super-important view gap-bottom">
        <div class="status-item">
          <div class="datum">LST:</div>
          <div class="value">{{ lst }}</div>
        </div>
        <div class="status-item">
          <div class="datum">Altitude:</div>
          <div class="value">
            <indi-value
              :indi-id="`${thisDeviceName}.telpos.el`"
              :formatFunction="(v) => String(Number(v).toFixed(4))"
            ></indi-value>º
          </div>
        </div>
        <div class="status-item">
          <div class="datum">Azimuth:</div>
          <div class="value">
            <indi-value
              :indi-id="`${thisDeviceName}.teldata.az`"
              :formatFunction="(v) => String(Number(v).toFixed(4))"
            ></indi-value>º
          </div>
        </div>
        <div class="status-item">
          <div class="datum">PA:</div>
          <div class="value">
          <indi-value
            :indi-id="`${thisDeviceName}.teldata.pa`"
            :formatFunction="(v) => String(Number(v).toFixed(4))"
          ></indi-value>
          </div>
        </div>
        <div class="status-item">
          <div class="datum">RA:</div>
          <div class="value">
            <indi-value
              :indi-id="`${thisDeviceName}.catdata.ra`"
              :formatFunction="decimalDegreesToTime"
            ></indi-value>
          </div>
        </div>
        <div class="status-item">
          <div class="datum">Dec:</div>
          <div class="value">
            <indi-value :indi-id="`${thisDeviceName}.catdata.dec`"></indi-value>º
          </div>
        </div>
        <div class="status-item">
          <div class="datum">HA:</div>
          <div class="value">
            <indi-value
              :indi-id="`${thisDeviceName}.telpos.ha`"
              :formatFunction="decimalHoursToTime"
            ></indi-value>
          </div>
        </div>
        <div class="status-item">
          <div class="datum">Epoch:</div>
          <div class="value">
            <indi-value
              :indi-id="`${thisDeviceName}.telpos.epoch`"
              :formatFunction="(v) => String(Number(v).toFixed(1))"
            ></indi-value>
          </div>
        </div>
        <div class="status-item">
          <div class="datum">Object:</div>
          <div class="value">
            <indi-value
              :indi-id="`${thisDeviceName}.catalog.object`"
            ></indi-value>
          </div>
        </div>
      </div>
      <observability-plots :equatorialCoords="equatorialCoords"></observability-plots>
  </div>
  <div v-else class="view">Waiting for tcsi...</div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.plots img {
  display: block;
  width: 100%;
}

.status-item {
  display: flex;
}
.datum {
  color: $alternate-gray;
}
.value {
  flex: 1;
  text-align: right;
}

.super-important {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-gap: 0 2 * $unit;
  font-size: 125%;
  padding: $unit;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiValue from "../indi/IndiValue.vue";
import ObservabilityPlots from '../plots/ObservabilityPlots.vue';

export default {
  props: ["device", "indiId"],
  mixins: [indi, utils],
  components: {
    IndiValue,
    ObservabilityPlots,
  },
  methods: {
    decimalHoursToTime(value) {
      const hours = String(Math.floor(value)).padStart(2, "0");
      let fracHour = value - hours;
      const minutes = String(Math.floor(fracHour * 60)).padStart(2, "0");
      fracHour = fracHour - minutes / 60;
      const seconds = String(Math.floor(60 * 60 * fracHour)).padStart(2, "0");
      return `${hours}:${minutes}:${seconds}`;
    },
    decimalDegreesToTime(value) {
      let origHours = (value / 360) * 24;
      const hours = String(Math.floor(origHours)).padStart(2, "0");
      let fracHour = origHours - hours;
      const minutes = String(Math.floor(fracHour * 60)).padStart(2, "0");
      fracHour = fracHour - minutes / 60;
      const seconds = String(Math.floor(60 * 60 * fracHour)).padStart(2, "0");
      return `${hours}:${minutes}:${seconds}`;
    },
  },
  computed: {
    lst() {
      if (this.indiDefined && this.thisDevice.teltime) {
        const teltime = this.thisDevice.teltime;
        return this.decimalHoursToTime(teltime._elements.sidereal_time._value);
      }
      return "";
    },
    airmassPlot() {
      if (!this.connected) {
        return "";
      }
      const catdata = this.thisDevice.catdata;
      return `/airmass?ra=${catdata._elements.ra._value}&dec=${catdata._elements.dec._value}`;
    },
    equatorialCoords() {
      const catdata = this.thisDevice.catdata;
      return {
        ra: catdata._elements.ra._value,
        dec: catdata._elements.dec._value,
      };
    }
  },
};
</script>