<template>
  <div id="app">
    <div class="status-bar">
      <div class="time">{{ readableTimestamp }}</div>
      <div class="logo">MagAO-X</div>
      <div class="connection">Connection: <indi-state-indicator :state="connectionStatus"></indi-light></div>
    </div>
    <div class="flex-row">
      <div class="vertical-selector">
        <router-link to="/" class="choice controls">
          <span class="nav-icon"><i class="material-icons">settings_applications</i></span>
          <span class="label">controls</span>
        </router-link>
        <router-link to="/power" class="choice power">
          <span class="nav-icon"><i class="material-icons">emoji_objects</i></span>
          <span class="label">power</span>
        </router-link>
        <router-link to="/properties" class="choice properties">
          <span class="nav-icon"><i class="material-icons">memory</i></span>
          <span class="label">properties</span>
        </router-link>
        <router-link to="/dashboard" class="choice dashboard">
          <div class="nav-icon"><i class="material-icons">dashboard</i></div>
          <div class="label">dashboard</div>
        </router-link>
        <router-link to="/bench" class="choice bench">
          <span class="nav-icon"><i class="material-icons">build</i></span>
          <span class="label">bench</span>
        </router-link>
        <router-link to="/kitchensink" class="choice">
          <span class="nav-icon"><i class="material-icons">build</i></span>
          <span class="label">kitchen sink</span>
        </router-link>
      </div>
      <div class="content">
        <keep-alive>
          <router-view></router-view>
        </keep-alive>
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
    display: block;
    &.controls {
      color: $warning;
    }
    &.power {
      color: $primary;
    }
  }
  .choice.router-link-exact-active {
    background: $base02;
    color: $linkActive;
  }
  .nav-icon {
    display: block;
  }
  .material-icons { font-size: 2*$unit; margin: 0}
}
.content {
  flex: 1;
}
</style>
<script>
import Vue from "vue";
import io from 'socket.io-client';
import IndiStateIndicator from "~/components/indi/IndiStateIndicator.vue";
import constants from "./constants.js";
import { DateTime } from "luxon";
import utils from "~/mixins/utils.js";

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
  mixins: [utils],
  components: {
    IndiStateIndicator,
  },
  inject: ["time"],
  // methods: {
  //   deviceChange: function (payload) {
  //     console.log("Device change:", payload);
  //     this.$socket.emit('indi_new', payload);
  //   }
  // },
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
});
</script>


