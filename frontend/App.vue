<template>
  <div id="app">
    <flames :active="showFlames"></flames>
    <div class="status">
      <div class="status-indicator">{{ readableTimestamp }}</div>
      <status-indicator :state="webSocketConnectionStatus" label="WS" icon-ok="link" icon-alert="link_off"></status-indicator>
      <status-indicator :state="indiConnectionStatus" label="INDI" icon-ok="link" icon-alert="link_off"></status-indicator>
      <loop-state indi-id="holoop"></loop-state>
    </div>
    <TabBar></TabBar>
    <observation-warnings></observation-warnings>
    <!-- <div class="flex-row"> -->
      <div class="content">
        <keep-alive>
          <router-view></router-view>
        </keep-alive>
      </div>
    <!-- </div> -->
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
#app {
  margin: 0 auto;
  // max-width: 80rem;
  // padding-bottom: 25vh;
  height: 100%;
}
.devices {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}

.status {
  color: $icon-gray;
  background: #1f1f1f;
  background: linear-gradient(180deg,#1f1f1f 0%,#000);
  flex: 1;
  padding-right: 1rem;
  box-sizing: border-box;
  display: flex;
  & > * {
    margin: $smgap $medgap;
  }
}

.status-bar {
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5 * $unit;
  margin-bottom: $unit;
  display: flex;
  div {
    flex: 2;
  }
  .status-left {
    text-align: left;
  }
  .logo {
    flex: 1;
    text-align: center;
    background-image: url(~/css/images/magao-x-white.svg);
    background-position: center center;
    background-repeat: no-repeat;
    text-indent: -9999px;
  }
  .status-right {
    text-align: right;
  }
}
// .content {
//   flex: 1;
//   overflow: hidden;
// }
.content {
  overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
  transition-property: opacity;
  transition-duration: 0.25s;
}

.fade-enter-active {
  transition-delay: 0.25s;
}

.fade-enter,
.fade-leave-active {
  opacity: 0;
}

  .nav-icon {
    display: inline-block;
    vertical-align: middle;
  }
  .material-icons {
    font-size: 2 * $unit;
    margin: 0;
  }
</style>
<script>
import Vue from "vue";
import io from "socket.io-client";
import IndiStateIndicator from "~/components/indi/IndiStateIndicator.vue";
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import TabBar from "~/components/basic/TabBar.vue";
import LoopState from "~/components/instrument/LoopState.vue";
import StatusIndicator from "~/components/basic/StatusIndicator.vue";
import constants from "./constants.js";
import ObservationWarnings from "~/components/instrument/ObservationWarnings.vue";
import Flames from "~/components/basic/Flames.vue";
import { DateTime } from "luxon";
import utils from "~/mixins/utils.js";

const cameraGroup = {
  filterWheel: null,
  focusStage: null,
  exposureTime: null,
  adcSpeed: null,
  gain: null,
  regionOfInterest: null,
  streamWriter: null
};

export default Vue.extend({
  mixins: [utils],
  components: {
    IndiStateIndicator,
    Flames,
    ToggleSwitch,
    TabBar,
    LoopState,
    StatusIndicator,
    ObservationWarnings
  },
  data: function () {
    return {
      flamesEnabled: false,
    };
  },
  inject: ["time", "indi" ],
  provide() {
    return {
      toggleFlames: this.toggleFlames,
    };
  },  
  methods: {
    toggleFlames() {
      this.flamesEnabled = !this.flamesEnabled;
    }, 
  },
  computed: {
    devices() {
      return this.indi.world.devices;
    },
    loopClosed () {
      let elt = this.retrieveByIndiId('aoloop.loopState.state');
      return elt && elt._value == 'closed';
    },
    showFlames() {
      return this.flamesEnabled;
    },
    readableTimestamp() {
      return (
        this.time.currentTime.toLocaleString(DateTime.DATE_MED) +
        " " +
        this.time.currentTime.toLocaleString(DateTime.TIME_24_WITH_SHORT_OFFSET)
      );
    },
    webSocketConnectionStatus() {
      return this.indi.webSocketIsConnected ? "ok" : "alert";
    },
    indiConnectionStatus() {
      if (this.indi.indiIsConnected && this.indi.lastUpdate !== null) {
        const delay = this.time.currentTime.diff(this.indi.lastUpdate, 'seconds');
        if (delay.seconds < constants.MAX_LASTUPDATE_DELTA_SEC) {
          return 'ok'
        }
      }
      return "alert";
    }
  }
});
</script>


