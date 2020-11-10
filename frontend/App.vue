<template>
  <div id="app">
    <flames :active="showFlames" :disabled="!loopClosed"></flames>
    <nav class="top">
      <div class="status">
        <div>
          <div class="logo">MagAO-X</div>
        </div>
          <div>{{ readableTimestamp }}</div>
          <div>WebSocket:
        <indi-state-indicator :state="webSocketConnectionStatus"></indi-state-indicator></div>
          <div>INDI:
        <indi-state-indicator :state="indiConnectionStatus"></indi-state-indicator></div>
          <div><loop-state indiId="aoloop"></loop-state></div>
        
      </div>
      <div class="tab-bar">
        <!-- <li class="tab active"><span class="icon"></span>active</li> -->
        <router-link to="/" class="tab btn cameras">
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
            <i class="material-icons">emoji_objects</i>
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

#app {
  margin: 0 auto;
  // max-width: 80rem;
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
  border-bottom: 1px solid $plasma-blue;
  display: flex;
  flex-flow: row-reverse wrap;
  margin-bottom: $lggap;
}

nav.top .status {
  color: var(--fg-normal);
  vertical-align: middle;
  // width: 15vw;
  // overflow: hidden;
  // position: absolute;
  // right: 0;
  // top: 0;
  flex: 1;
  padding-top: 1rem;
  padding-right: 1rem;
  box-sizing: border-box;
  display: flex;
  flex-direction: row-reverse;
  // .col {
  //   display: flex;
  //   flex-direction: column;
  // }
}

nav.top .tab-bar {
  display: flex;
  padding: 1rem 1rem 0rem 1rem;
  margin: 0;
  .tab {
    // background: var(--bg-normal);
    display: block;
    padding: 1rem;
    border-top: 1px solid var(--border);
    border-right: 1px solid var(--border);
    border-bottom: none;
    &:first-child {
      border-left: 1px solid var(--border);
    }
    // &.active {
    //   background: $plasma-blue;
    //   // color: var(--charcoal-gray);
    //   // border: 1px solid $plasma-blue;
    // }
    &:hover, &.router-link-exact-active {
      color: var(--fg-normal);
      background: $plasma-blue;
      border-top: 1px solid $plasma-blue;
      border-right: 1px solid $plasma-blue;
      &:first-child {
        border-left: 1px solid $plasma-blue;
      }
    }
  }
}

.logo {
  // flex: 1;
  min-width: 170px;
  min-height: 40px;
  text-align: center;
  background-image: url(~/css/images/magao-x-white.svg);
  background-position: center center;
  background-size: 100%;
  background-repeat: no-repeat;
  text-indent: -9999px;
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
  .status-right {
    text-align: right;
  }
}
// .vertical-selector {
//   margin-right: $unit;
//   text-align: center;
//   width: 100px;

//   .choice {
//     padding: 0.5 * $unit;
//     display: block;
//     border: 1px solid var(--border);
//     margin: 10px 0;
//     &:nth-child(1) {
//       color: $icon-red;
//       border-color: $icon-red;
//       &.router-link-exact-active {
//         color: var(--bg-normal);
//         background: $icon-red;
//       }
//     }
//     &:nth-child(2) {
//       color: $icon-violet;
//       border-color: $icon-violet;
//       &.router-link-exact-active {
//         color: var(--bg-normal);
//         background: $icon-violet;
//       }
//     }
//     &:nth-child(3) {
//       color: $icon-blue;
//       border-color: $icon-blue;
//       &.router-link-exact-active {
//         color: var(--bg-normal);
//         background: $icon-blue;
//       }
//     }
//     &:nth-child(4) {
//       color: $icon-green;
//       border-color: $icon-green;
//       &.router-link-exact-active {
//         color: var(--bg-normal);
//         background: $icon-green;
//       }
//     }
//     &:nth-child(5) {
//       color: $icon-yellow;
//       border-color: $icon-yellow;
//       &.router-link-exact-active {
//         color: var(--bg-normal);
//         background: $icon-yellow;
//       }
//     }
//     &:nth-child(6) {
//       color: $icon-orange;
//       border-color: $icon-orange;
//       &.router-link-exact-active {
//         color: var(--bg-normal);
//         background: $icon-orange;
//       }
//     }
//   }
  // .choice.router-link-exact-active {
  //   background: var(--bg-alternate);
  //   color: $linkActive;
  // }
//   .nav-icon {
//     display: block;
//   }
//   .material-icons {
//     font-size: 2 * $unit;
//     margin: 0;
//   }
// }
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
</style>
<script>
import Vue from "vue";
import io from "socket.io-client";
import IndiStateIndicator from "~/components/indi/IndiStateIndicator.vue";
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import LoopState from "~/components/instrument/LoopState.vue";
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
    ToggleSwitch,
    LoopState
  },
  data: function () {
    return {
      flamesEnabled: false
    };
  },
  inject: ["time"],
  methods: {
    toggleFlames() {
      this.flamesEnabled = !this.flamesEnabled;
    }
  },
  computed: {
    devices() {
      return this.$store.state.devices;
    },
    loopClosed () {
      let elt = this.retrieveByIndiId('aoloop.loopState.state');
      return elt && elt.value == 'closed';
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


