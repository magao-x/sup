<template>
  <div class="motion-stage">
    <div>{{ name }}</div>
    <div v-if="indiDefined" class="flex-row">
      <div class="ms-details">
        <div><finite-state-machine-status :device="thisDevice"></finite-state-machine-status></div>
        <indi-property :device="thisDevice" :property="positionProperty"></indi-property>
        <!-- <indi-value :indiId="thisDevice.name + '.' + presetBaseName + '.current'"></indi-value>
        <indi-element :indiId="thisDevice.name + '.' + presetBaseName + '.target'" inputWidth="5"></indi-element> -->
        <div style="display: flex; flex-wrap: wrap;">
          <button class="home" @click.prevent="sendHome">
            <i class="material-icons">home</i> home
          </button>
          <button class="stop" @click.prevent="sendStop">
            <i class="material-icons">block</i> stop
          </button>
        </div>
      </div>
      <div class="ms-friendly" v-if="indiDefined">
        <indi-switch-multi-element
          :orientation="orientation"
          :disabled="isDisabled"
          :device="thisDevice"
          :property="presetNames"
        ></indi-switch-multi-element>
      </div>

    </div>
    <div v-else>
      Waiting for device
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "~/css/variables.scss";
.motion-stage {
  flex: 1;
}
.ms-friendly,.ms-details {
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
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiElement from "~/components/indi/IndiElement.vue";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  mixins: [indi, utils],
  props: {
    device: Object,
    kind: {
      type: String,
      default: "stage"
    },
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
    FiniteStateMachineStatus,
    IndiProperty
  },
  methods: {
    sendHome: function() {
      if (!this.thisDevice) return;
      this.sendIndiNew(
        this.thisDevice,
        this.thisDevice.properties["home"],
        this.thisDevice.properties["home"].elements["request"],
        "On"
      );
    },
    sendStop: function() {
      if (!this.thisDevice) return;
      this.sendIndiNew(
        this.thisDevice,
        this.thisDevice.properties["stop"],
        this.thisDevice.properties["stop"].elements["request"],
        "On"
      );
    }
  },
  computed: {
    isDisabled: function() {
      if (!(this.thisDevice && this.thisDevice.properties["fsm"])) {
        return true;
      }
      const fsmState = this.thisDevice.properties["fsm"].elements["state"].value;
      return (
        !(fsmState == "READY" || fsmState == "OPERATING") ||
        this.presetNames.state == "Busy"
      );
    },
    presetNames: function() {
      const presetBaseName = (this.kind.toLowerCase() == "stage") ? "preset" : "filter";
      if (this.thisDevice && this.thisDevice.properties[presetBaseName + "Name"]) {
        return this.thisDevice.properties[presetBaseName + "Name"];
      } else {
        return null;
      }
    },
    positionProperty() {
      if (this.indiDefined) {
        if (this.kind.toLowerCase() == "stage") {
          return this.thisDevice.properties['position'];
        } else if (this.kind.toLowerCase() == "filterwheel") {
          return this.thisDevice.properties['filter'];
        }
      }

    },
    name: function() {
      if (this.label) {
        return this.label;
      } else if (this.thisDevice) {
        return this.thisDevice.name;
      } else {
        return this.indiId;
      }
    },
    fsmState: function() {
      if (this.thisDevice && this.thisDevice.properties["fsm"]) {
        return this.thisDevice.properties["fsm"].elements["state"].value;
      } else {
        return null;
      }
    }
  }
};
</script>