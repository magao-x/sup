<template>
  <div id="app">
    <flames :active="showFlames"></flames>
    <div class="status">
      <div class="status-indicator">{{ readableTimestamp }}</div>
      <status-indicator :state="webSocketConnectionStatus" label="WS" icon-ok="link" icon-alert="link_off"></status-indicator>
      <status-indicator :state="indiConnectionStatus" label="INDI" icon-ok="link" icon-alert="link_off"></status-indicator>
      <loop-state indi-id="holoop"></loop-state>
    </div>
    <nav class="top">
      <div id="logo">
        <img @click="toggleFlames" src="~/assets/magao-x_logo_white.svg">
      </div>
      <div class="tab-bar">
        <router-link to="/" class="tab btn observation">
          <span class="nav-icon">
            <i class="material-icons">visibility</i>
          </span>
          <span class="label">observation</span>
        </router-link>
        <router-link to="/cameras" class="tab btn cameras">
          <span class="nav-icon">
            <i class="material-icons">camera</i>
          </span>
          <span class="label">cameras</span>
        </router-link>
        <router-link to="/ao" class="tab btn ao">
          <span class="nav-icon">
            <i class="material-icons">blur_on</i>
          </span>
          <span class="label">AO</span>
        </router-link>
        <router-link to="/dashboard" class="tab btn dashboard">
          <span class="nav-icon">
            <i class="material-icons">speed</i>
          </span>
          <span class="label">dashboard</span>
        </router-link>
        <router-link to="/power" class="tab btn power">
          <span class="nav-icon">
            <i class="material-icons">power_settings_new</i>
          </span>
          <span class="label">power</span>
        </router-link>
        <router-link to="/lab" class="tab btn lab">
          <span class="nav-icon">
            <i class="material-icons">build</i>
          </span>
          <span class="label">lab</span>
        </router-link>
      </div>
    </nav>
    <observation-warnings></observation-warnings>
    <!-- <div class="status-bar">
      <div class="status-left">
        <div>{{ readableTimestamp }}</div>
        <loop-state indiId="aoloop"></loop-state>
      </div>
      <div class="logo" @click="toggleFlames">MagAO-X</div>
      <div class="status-right">
        <div>WebSocket:
        <indi-state-indicator :state="webSocketConnectionStatus"></indi-state-indicator></div>
        <div>INDI:
        <indi-state-indicator :state="indiConnectionStatus"></indi-state-indicator></div>
      </div>
    </div> -->
    <div class="flex-row">
      <!-- <div class="vertical-selector">
        <router-link to="/" class="choice cameras">
          <span class="nav-icon">
            <i class="material-icons">camera</i>
          </span>
          <span class="label">cameras</span>
        </router-link>
        <router-link to="/ao" class="choice ao">
          <span class="nav-icon">
            <i class="material-icons">blur_on</i>
          </span>
          <span class="label">AO</span>
        </router-link>
        <router-link to="/dashboard" class="choice dashboard">
          <div class="nav-icon">
            <i class="material-icons">speed</i>
          </div>
          <div class="label">dashboard</div>
        </router-link>
        <router-link to="/power" class="choice power">
          <span class="nav-icon">
            <i class="material-icons">emoji_objects</i>
          </span>
          <span class="label">power</span>
        </router-link>
        <router-link to="/lab" class="choice">
          <span class="nav-icon">
            <i class="material-icons">build</i>
          </span>
          <span class="label">lab</span>
        </router-link>
      </div> -->
      <div class="content">
        <keep-alive>
          <router-view></router-view>
        </keep-alive>
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

#logo {
  height: 100%;
  display: flex;
flex: 1;
position: relative;
 img {
    width: 168px;
    padding: 0 1rem;
    filter: drop-shadow(0px 0px 5px #3daee9);
    mix-blend-mode: screen;
    position: absolute;
    right: 0;
    top: 0.5rem;
  }
}


#app {
  margin: 0 auto;
  // max-width: 80rem;
  padding-bottom: 25vh;
}
.devices {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}

nav.top {
  position: relative;
  // padding-right: 15vw;
  background-color: var(--inset-bg);
  border-bottom: 3px solid $plasma-blue;
  display: flex;
  flex-flow: row-reverse wrap;
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

nav.top .tab-bar {
  display: flex;
  padding: 1rem 1rem 0rem 1rem;
  margin: 0;
  .tab {
    // background: var(--bg-normal);
    display: block;
    padding: calc($unit / 2);
    border-top: 1px solid var(--border);
    border-right: 1px solid var(--border);
    border-bottom: none;
    &:first-child {
      border-left: 1px solid var(--border);
    }
    text-decoration: none;
    .label {
      text-decoration: underline;
    }
    &:hover, &.router-link-exact-active {
      color: var(--fg-normal);
      background: $plasma-blue;
      border-top: 1px solid $plasma-blue;
      border-right: 1px solid $plasma-blue;
      // &:first-child {
        border-left: 1px solid $plasma-blue;
      // }
    }
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
.content {
  flex: 1;
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
    LoopState,
    StatusIndicator,
    ObservationWarnings,
  },
  data: function () {
    return {
      flamesEnabled: false
    };
  },
  inject: ["time", "indi"],
  methods: {
    toggleFlames() {
      this.flamesEnabled = !this.flamesEnabled;
    },
  },
  computed: {
    devices() {
      return this.$store.state.devices;
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
    }
  }
});
</script>


