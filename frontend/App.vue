<template>
  <div id="app">
    <flames :active="showFlames" :disabled="!loopClosed"></flames>
    <div class="status-bar">
      <div class="time">{{ readableTimestamp }}</div>
      <div class="logo">MagAO-X</div>
      <div class="status-right">
        <div><toggle-switch
          v-model="toggleFlames"
          labelOn="FLAMES"
          labelOff="NO"
        ></toggle-switch></div>
        <div>WebSocket:
        <indi-state-indicator :state="webSocketConnectionStatus"></indi-state-indicator>INDI:
        <indi-state-indicator :state="indiConnectionStatus"></indi-state-indicator></div>
      </div>
    </div>
    <div class="flex-row">
      <div class="vertical-selector">
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
@import "./css/variables.scss";

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
    flex: 2;
  }
  .time {
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
    display: flex;
  }
}
.vertical-selector {
  margin-right: $unit;
  text-align: center;
  width: 100px;

  .choice {
    padding: 0.5 * $unit;
    display: block;
    border: 1px solid $base01;
    margin: 10px 0;
    &:nth-child(1) {
      color: $red;
      border-color: $red;
      &.router-link-exact-active {
        color: $base03;
        background: $red;
      }
    }
    &:nth-child(2) {
      color: $magenta;
      border-color: $magenta;
      &.router-link-exact-active {
        color: $base03;
        background: $magenta;
      }
    }
    &:nth-child(3) {
      color: $violet;
      border-color: $violet;
      &.router-link-exact-active {
        color: $base03;
        background: $violet;
      }
    }
    &:nth-child(4) {
      color: $blue;
      border-color: $blue;
      &.router-link-exact-active {
        color: $base03;
        background: $blue;
      }
    }
    &:nth-child(5) {
      color: $cyan;
      border-color: $cyan;
      &.router-link-exact-active {
        color: $base03;
        background: $cyan;
      }
    }
    &:nth-child(6) {
      color: $green;
      border-color: $green;
      &.router-link-exact-active {
        color: $base03;
        background: $green;
      }
    }
    &:nth-child(7) {
      color: $yellow;
      border-color: $yellow;
      &.router-link-exact-active {
        color: $base03;
        background: $yellow;
      }
    }
    &:nth-child(8) {
      color: $orange;
      border-color: $orange;
      &.router-link-exact-active {
        color: $base03;
        background: $orange;
      }
    }
  }
  .choice.router-link-exact-active {
    background: $base02;
    color: $linkActive;
  }
  .nav-icon {
    display: block;
  }
  .material-icons {
    font-size: 2 * $unit;
    margin: 0;
  }
}
.content {
  flex: 1;
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
</style>
<script>
import Vue from "vue";
import io from "socket.io-client";
import IndiStateIndicator from "~/components/indi/IndiStateIndicator.vue";
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import constants from "./constants.js";
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
    ToggleSwitch
  },
  data: function () {
    return {
      toggleFlames: false
    };
  },
  inject: ["time"],
  computed: {
    devices() {
      return this.$store.state.devices;
    },
    loopClosed () {
      let elt = this.retrieveByIndiId('aoloop.loopState.state');
      console.log(elt);
      return elt && elt.value == 'closed';
    },
    showFlames() {
      return this.loopClosed && this.toggleFlames;
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


