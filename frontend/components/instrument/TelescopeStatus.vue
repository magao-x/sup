<template>
  <div class="view" v-if="indiDefined">
    {{ lst }}
    <div class="cols">
      <div class="col">
        <div>Catalog</div>
        <div>
          RA:
          <indi-value :indi-id="`${thisDevice.name}.catdata.ra`" :formatFunction="decimalDegreesToTime"></indi-value>
        </div>
        <div>
          Dec:
          <indi-value :indi-id="`${thisDevice.name}.catdata.dec`"></indi-value>
        </div>
        <div>
          Epoch:
          <indi-value
            :indi-id="`${thisDevice.name}.catdata.epoch`"
          ></indi-value>
        </div>
        <div>
          Object:
          <indi-value
            :indi-id="`${thisDevice.name}.catalog.object`"
          ></indi-value>
        </div>
      </div>
      <div class="col">
        <div>Current</div>
        <div>
          Az:
          <indi-value :indi-id="`${thisDevice.name}.teldata.az`"></indi-value>
        </div>
        <div>
          El:
          <indi-value :indi-id="`${thisDevice.name}.telpos.el`"></indi-value>
        </div>
        <div>
          HA:
          <indi-value :indi-id="`${thisDevice.name}.telpos.ha`" :formatFunction="decimalHoursToTime"></indi-value>
        </div>
        <div>
          RA:
          <indi-value :indi-id="`${thisDevice.name}.telpos.ra`" :formatFunction="decimalDegreesToTime"></indi-value>
        </div>
        <div>
          Dec:
          <indi-value :indi-id="`${thisDevice.name}.telpos.dec`"
            :formatFunction="(v) => Number(v).toFixed(4)"
          ></indi-value>º
        </div>
        <div>
          Epoch:
          <indi-value
            :indi-id="`${thisDevice.name}.telpos.epoch`"
            :formatFunction="(v) => String(Number(v).toFixed(1))"
          ></indi-value>
        </div>
      </div>
      <div class="col">
        <nudger></nudger>
      </div>
    </div>
  </div>
  <div v-else class="view">Waiting for tcsi...</div>
</template>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiValue from "../indi/IndiValue.vue";
import Nudger from "~/components/instrument/Nudger.vue";

export default {
  props: ["device", "indiId"],
  mixins: [indi, utils],
  components: {
    IndiValue,
    Nudger,
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
      let origHours = value / 360 * 24;
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
      if (!this.indiDefined) {
        return "";
      }
      const telpos = this.thisDevice.properties.telpos;
      const raHours = telpos.elements.ra.value / 360 * 24;
      return this.decimalHoursToTime(raHours + telpos.elements.ha.value);
    }
  }
};
</script>