<template>
  <div class="telescope-status" v-if="indiDefined">
    <div class="date-utc gap-bottom">
      <div style="text-align: right">
        {{ readableTimestamp }}
      </div>
      <div style="text-align: left">
        {{ readableDatestamp }}
      </div>
    </div>
    <div class="super-important view gap-bottom">
      <div class="status-item">
        <div class="datum">Object:</div>
        <div class="value">
          <indi-value
          :indi-id="`${thisDeviceName}.catalog.object`"
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
          <div class="datum">Declination:</div>
          <div class="value">
            <indi-value
              :indi-id="`${thisDeviceName}.catdata.dec`"
              :formatFunction="decimalDegreesToDMS"
            ></indi-value>
          </div>
        </div>
      <div class="status-item">
        <div class="datum">LST:</div>
        <div class="value">{{ lst }}</div>
      </div>
      <div class="status-item">
        <div class="datum">Hour Angle:</div>
        <div class="value">
          <indi-value
              :indi-id="`${thisDeviceName}.telpos.ha`"
              :format-function="decimalHoursToTimeEastWest"
          ></indi-value>
        </div>
      </div>
      <div class="status-item">
        <div class="datum">PA:</div>
        <div class="value">
          <indi-value
          :indi-id="`${thisDeviceName}.teldata.pa`"
          :formatFunction="(v) => String(Number(v).toFixed(2)) + 'º'"
          ></indi-value>
        </div>
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
          <div class="datum">Airmass:</div>
          <div class="value">
            {{ airmass }}
          </div>
        </div>
      </div>
      <!-- <div class="status-tiles gap-bottom">
        <div class="status-tile view">
          <div>
            <span class="name">seeing</span>
          </div>
          <span v-if="retrieveValueByIndiId('tcsi.seeing.mag1_fwhm_corr') > 0">
            Baade: <indi-value indi-id="tcsi.seeing.mag1_fwhm_corr"></indi-value>&Prime;
          </span>
          <span v-else>
            no Baade
          </span>
          <br>
          <span v-if="retrieveValueByIndiId('tcsi.seeing.dimm_fwhm') > 0">
            DIMM: <indi-value indi-id="tcsi.seeing.dimm_fwhm"></indi-value>&Prime;
          </span>
          <span v-else>
            no DIMM
          </span>
        </div>
        <div class="status-tile view">
          <div>
            <span class="name">wind</span>
          </div>
          <indi-value indi-id="tcsi.environment.wind"></indi-value> Mph
          <br>@ <indi-value
          indi-id="tcsi.environment.winddir"></indi-value>º
        </div>
        <div class="status-tile view">
          <div>
            <span class="name">humidity / dewpoint</span>
          </div>
          <indi-value indi-id="tcsi.environment.humidity"></indi-value>%
          <br>
          <indi-value indi-id="tcsi.environment.dewpoint"></indi-value>ºC
        </div>
        <div class="status-tile view">
            <div>
              <span class="name">ambient temp.</span>
            </div>
            <indi-value indi-id="tcsi.environment.temp-amb"></indi-value>ºC
          </div>
      </div> -->
      <!-- <observability-plots
        :equatorialCoords="equatorialCoords"
        :beginObsTimestamp="beginObsTimestamp"></observability-plots> -->
    </div>
    <div v-else class="view">Waiting for tcsi...</div>
  </template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.plots img {
  display: block;
  width: 100%;
}

.status-tiles {
  grid-template-columns: 1fr 1fr 1fr 1fr;
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
.date-utc {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-gap: 0 2 * $unit;
  font-size: 150%;
  padding: 0.125rem;
  font-weight: bold;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiValue from "~/components/indi/IndiValue.vue";
import ObservabilityPlots from '~/components/plots/ObservabilityPlots.vue';
import { DateTime } from "luxon";

export default {
  props: ["device", "indiId"],
  mixins: [indi, utils],
  components: {
    IndiValue,
    ObservabilityPlots,
  },
  methods: {
    decimalHoursToTime(value) {
      let sign = value / Math.abs(value);
      let hours = Math.floor(value / sign);
      let fracHour = (value / sign) - hours;
      const minutes = String(Math.floor(fracHour * 60)).padStart(2, "0");
      fracHour = fracHour - minutes / 60;
      const seconds = String(Math.floor(60 * 60 * fracHour)).padStart(2, "0");
      let signMark = sign == -1 ? "-" : "";
      return `${signMark}${hours}:${minutes}:${seconds}`;
    },
    decimalHoursToTimeEastWest(value) {
      let sign = Math.sign(value);
      let hours = Math.floor(value / sign);
      let fracHour = (value / sign) - hours;
      const minutes = String(Math.floor(fracHour * 60)).padStart(2, "0");
      fracHour = fracHour - minutes / 60;
      const seconds = String(Math.floor(60 * 60 * fracHour)).padStart(2, "0");
      let signMark;
      if (sign == 1) {
        signMark = "W ";
      } else {
        signMark = "E ";
      }
      return `${signMark}${hours}:${minutes}:${seconds}`;
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
    decimalDegreesToDMS(value) {
      const sign = Math.sign(value);
      const deg = Math.floor(value / sign);
      let fracDeg = (value/sign - deg) * 60;
      const min = String(Math.floor(fracDeg)).padStart(2, "0");
      fracDeg = (fracDeg - Math.floor(fracDeg)) * 60;
      const sec = String(Math.floor(fracDeg)).padStart(2, "0");
      const signString = (sign == 1) ? '+' : '-';
      return `${signString}${deg}º${min}'${sec}"`;
    },
  },
  computed: {
    readableDatestamp() {
      return (
        this.time.currentTime.toLocaleString(DateTime.DATE_MED) 
        // +
        // " " +
        // this.time.currentTime.toLocaleString(DateTime.TIME_24_WITH_SHORT_OFFSET)
      );
    },
    readableTimestamp() {
      return (
        // this.time.currentTime.toLocaleString(DateTime.DATE_MED) +
        // " " +
        this.time.currentTime.toLocaleString(DateTime.TIME_24_WITH_SHORT_OFFSET)
      );
    },
    beginObsTimestamp() {
      return null;
      let positionProp = this.thisDevice?.catalog;
      if (positionProp) {
        console.log(positionProp.timestamp);
        return positionProp.timestamp;
      } else {
        return null;
      }
    },
    airmass() {
      if (this.indiDefined && this.thisDevice.telpos) {
        const telpos = this.thisDevice.telpos;
        const elevationDeg = telpos._elements.el._value;
        const airmassValue = 1 / Math.cos((90 - elevationDeg) / 180 * Math.PI);
        return airmassValue.toFixed(3);
      }
      return "";
    },
    lst() {
      if (this.indiDefined && this.thisDevice.teltime) {
        const teltime = this.thisDevice.teltime;
        return this.decimalHoursToTime(teltime._elements.sidereal_time._value);
      }
      return "";
    },
    airmassPlot() {
      if (!this.indi.connected) {
        return "";
      }
      const catdata = this.thisDevice.catdata;
      return `/airmass?ra=${catdata._elements.ra._value}&dec=${catdata._elements.dec._value}`;
    },
  },
};
</script>