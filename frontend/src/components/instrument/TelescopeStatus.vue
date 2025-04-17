<template>
  <div class="telescope-status" v-if="indiDefined">
    <div class="date-time view padded">
      <div class="full-width">
        <indi-value :indi-id="`${thisDeviceName}.catalog.object`"></indi-value>
      </div>
      <div class="label">
        RA
      </div>
      <div class="value">
        <indi-value :indi-id="`${thisDeviceName}.catdata.ra`" :formatFunction="decimalDegreesToTime"></indi-value>
      </div>
      <div class="label">LST</div>
      <div class="value">{{ lst }}</div>
      <div class="label">HA</div>
      <div class="sign">
        <indi-value :indi-id="`${thisDeviceName}.telpos.ha`" :format-function="decimalHoursToEastWest"></indi-value>
      </div>
      <div>
        <indi-value :indi-id="`${thisDeviceName}.telpos.ha`" :format-function="decimalHoursToTimeUnsigned"></indi-value>
      </div>
    </div>
    <div class="environment view padded">
      <div class="label">Temp.</div><div class="value">{{ retrieveValueByIndiId('tcsi.environment.temp-amb') }} ºC</div>
      <div class="label">Dewpoint</div><div class="value">{{ retrieveValueByIndiId('tcsi.environment.dewpoint') }} ºC</div>
      <div class="label">Humidity</div><div class="value">{{ retrieveValueByIndiId('tcsi.environment.humidity') }}%</div>
      <div class="label">Wind</div><div class="value">{{ retrieveValueByIndiId('tcsi.environment.wind') }} MPH</div>
      <div class="label">Wind Dir.</div><div class="value">{{ retrieveValueByIndiId('tcsi.environment.winddir') }}º</div>
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

    <observability-plots class="observability-plots" :equatorialCoords="equatorialCoords"
      :beginObsTimestamp="beginObsTimestamp" observersDevice="observers"></observability-plots>
  </div>
  <div v-else class="view">Waiting for tcsi...</div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.telescope-status {
  display: grid;
  grid-template-columns: subgrid;
  grid-template-rows: subgrid;
  height: 100%;
}

.observability-plots {
  grid-column: 3/11;
  grid-row: 1/5;
}

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

.status-item .value {
  flex: 1;
  text-align: right;
}



.date-time, .environment {
  grid-column: 1/3;
}

.environment {
  grid-row: 3/5;
}

.date-time {
  grid-row: 1/3;
  font-size: 150%;
  font-weight: bold;
  color: var(--fg-neutral);
}

.date-time, .environment {
  display: grid;
  padding: $lggap;
  grid-template-columns: calc(50% - $unit) 20px calc(50% - 20px - $unit);
  grid-gap: 0 $unit;
  .full-width {
    grid-column: 1/4;
    text-align: center;
  }
  .label {
    grid-column: 1;
    text-align: right
  }
  .sign {
    grid-column: 2;
  }
  .value {
    grid-column: 3;
  }
}
</style>
<script>
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";
import IndiValue from "@/components/indi/IndiValue.vue";
import ObservabilityPlots from '@/components/plots/ObservabilityPlots.vue';

export default {
  props: ["device", "indiId"],
  mixins: [indi, utils],
  components: {
    IndiValue,
    ObservabilityPlots,
  },
  methods: {
    decimalHoursToTime(value) {
      if (value == 0) {
        return '00:00:00';
      }
      let sign = value / Math.abs(value);
      let signMark = sign == -1 ? "-" : "";
      return `${signMark}${this.decimalHoursToTimeUnsigned(value)}`;
    },
    decimalHoursToTimeUnsigned(value) {
      if (value == 0) {
        return '00:00:00';
      }
      let sign = value / Math.abs(value);
      let hours = Math.floor(value / sign);
      let fracHour = (value / sign) - hours;
      let hoursStr = String(hours).padStart(2, "0");
      const minutes = String(Math.floor(fracHour * 60)).padStart(2, "0");
      fracHour = fracHour - minutes / 60;
      const seconds = String(Math.floor(60 * 60 * fracHour)).padStart(2, "0");
      return `${hoursStr}:${minutes}:${seconds}`;
    },
    decimalHoursToEastWest(value) {
      const sign = Math.sign(value);
      if (sign == 1) {
        return "W";
      } else {
        return "E";
      }
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
      let fracDeg = (value / sign - deg) * 60;
      const min = String(Math.floor(fracDeg)).padStart(2, "0");
      fracDeg = (fracDeg - Math.floor(fracDeg)) * 60;
      const sec = String(Math.floor(fracDeg)).padStart(2, "0");
      const signString = (sign == 1) ? '+' : '-';
      return `${signString}${deg}º${min}'${sec}"`;
    },
  },
  computed: {
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
    equatorialCoords() {
      let catData = this.retrieveByIndiId('tcsi.catdata');
      if (catData) {
        return {
          ra: catData._elements.ra._value,
          dec: catData._elements.dec._value,
        };
      }
    }
  },
};
</script>