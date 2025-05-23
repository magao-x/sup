<template>
  <div class="filter-wheel">
    <div>{{ name }}</div>
    <div class="flex-row">
      <div class="fw-details">
        <div><finite-state-machine-status :device="thisDevice"></finite-state-machine-status></div>
        <indi-value :indiId="thisDeviceName + '.filter.current'"></indi-value>
        <indi-element :indiId="thisDeviceName + '.filter.target'" inputWidth="5"></indi-element>
      </div>
      <div class="fw-friendly">
        <div style="display: flex; flex-wrap: wrap;">
          <button class="home" @click.prevent="sendHome">
            <i class="material-icons">home</i> home
          </button>
          <button class="stop" @click.prevent="sendStop">
            <i class="material-icons">block</i> stop
          </button>
        </div>
        <indi-switch-multi-element
          :orientation="orientation"
          :disabled="isDisabled"
          :device="thisDevice"
          :property="filterNames"
        ></indi-switch-multi-element>
      </div>

    </div>
  </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss";
.filter-wheel {
  margin: 1rem;
  flex: 1;
}
.fw-friendly,.fw-details {
  width: 50%;
  margin: 10px;
  box-sizing: border-box;
}
button.home {
  background-color: $yellow;
}
button.stop {
  background-color: $red;
}
</style>
<script>
import IndiElement from "@/components/indi/IndiElement.vue";
import IndiValue from "@/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "@/components/indi/IndiSwitchMultiElement.vue";
import FiniteStateMachineStatus from "@/components/instrument/FiniteStateMachineStatus.vue";
import indi from "@/mixins/indi.js";

export default {
  mixins: [indi],
  props: {
    device: Object,
    indiId: String,
    label: String,
    orientation: {
      type: String,
      default: "horizontal"
    }
  },
  components: {
    IndiSwitchMultiElement,
    IndiElement,
    IndiValue,
    FiniteStateMachineStatus
  },
  methods: {
    sendHome: function() {
      if (!this.thisDevice) return;
      this.sendIndiNew(
        this.thisDevice["home"],
        this.thisDevice["home"]._elements["request"],
        "On"
      );
    },
    sendStop: function() {
      if (!this.thisDevice) return;
      this.sendIndiNew(
        this.thisDevice["stop"],
        this.thisDevice["stop"]._elements["request"],
        "On"
      );
    }
  },
  computed: {
    isDisabled: function() {
      if (!(this.thisDevice && this.thisDevice["fsm"])) {
        return true;
      }
      const fsmState = this.thisDevice["fsm"]._elements["state"]
        .value;
      return (
        !(fsmState == "READY" || fsmState == "OPERATING") ||
        this.filterNames.state == "Busy"
      );
    },
    filterNames: function() {
      if (this.thisDevice && this.thisDevice["filterName"]) {
        return this.thisDevice["filterName"];
      } else {
        return null;
      }
    },
    name: function() {
      if (this.label) {
        return this.label;
      } else if (this.thisDevice) {
        return this.thisDeviceName;
      } else {
        return this.indiId;
      }
    },
    fsmState: function() {
      if (this.thisDevice && this.thisDevice["fsm"]) {
        return this.thisDevice["fsm"]._elements["state"]._value;
      } else {
        return null;
      }
    }
  }
};
</script>