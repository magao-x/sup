<template>
  <div id="app">
    <div class="status-bar">
      <div class="time">{{ readableTimestamp }}</div>
      <div class="logo">MagAO-X</div>
      <div class="connection">Connection: <indi-light :state="connectionStatus"></indi-light></div>
    </div>
    <div class="flex-row">
      <div class="vertical-selector">
        <div class="choice">
          <div><i class="material-icons">settings_applications</i></div>
          <div class="label">controls</div>
        </div>
        <div class="choice active">
          <div class="icon"><i class="material-icons">memory</i></div>
          <div class="label">properties</div>
        </div>
        <div class="choice">
          <div><i class="material-icons">dashboard</i></div>
          <div class="label">dashboard</div>
        </div>
      </div>
      <div class="content">
        <indi-properties-table :devices="devices"></indi-properties-table>
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';
#app {
  margin: 0 auto;
  max-width: 80rem;
}
.devices {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}
.status-bar {
  border-bottom: 1px solid $base01;
  padding-bottom: 0.5 * $unit;
  margin-bottom: $unit;
  display: flex;
  div {
    flex: 1
  }
  .time { text-align: left; }
  .logo {
    text-align: center;
    background-image: url(~/css/images/magao-x-white.svg);
    background-position: center center;
    background-repeat: no-repeat;
    text-indent: -9999px;
  }
  .connection { text-align: right; }
}
.vertical-selector {
  margin-right: $unit;
  text-align: center;
  .choice {
    padding: 0.5*$unit;
  }
  .choice.active {
    background: $base02;
  }
  .material-icons { font-size: 2*$unit; margin: 0}
}
.content {
  flex: 1;
  overflow-y: scroll;
}
</style>
<script>
import Vue from "vue";
import io from 'socket.io-client';
import IndiDevice from "./IndiDevice.vue";
import IndiLight from "./IndiLight.vue";
import IndiPropertiesTable from "./IndiPropertiesTable.vue";
import IndiSwitchMultiElement from "./IndiSwitchMultiElement.vue";
import utils from "./utils.js";
import constants from "./constants.js";
import { DateTime } from "luxon";

const cameraGroup = {
  filterWheel: null,
  focusStage: null,
  exposureTime: null,
  adcSpeed: null,
  gain: null,
  regionOfInterest: null,
  streamWriter: null,
}

export default Vue.extend({
  components: {
    IndiDevice,
    IndiLight,
    IndiSwitchMultiElement,
    IndiPropertiesTable
  },
  inject: ["time"],
  methods: {
    deviceChange: function (payload) {
      console.log("Device change:", payload);
      this.$socket.emit('indi_new', payload);
    }
  },
  computed: {
    connection () {
      return this.$store.state.connection
    },
    connectionStatus() {
      if (!this.$store.state.connection.connected) {
        return 'Alert';
      }
      const delay = this.time.currentTime.diff(this.$store.state.connection.lastUpdate, 'seconds');
      if (delay.seconds < constants.MAX_LASTUPDATE_DELTA_SEC) {
        return 'Ok'
      } else {
        return 'Alert'
      }
    },
    devices() {
      return this.$store.state.devices
    },
    readableTimestamp() {
      return (this.time.currentTime.toLocaleString(DateTime.DATE_MED) + " " +
              this.time.currentTime.toLocaleString(DateTime.TIME_24_WITH_SHORT_OFFSET));
    }
  },
  mixins: [utils]
});
</script>


