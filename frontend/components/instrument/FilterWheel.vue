<template>
  <div class="filter-wheel">
    <div>{{ name }}</div>
    <div>{{ fsmState }}</div>
    <indi-value :indiId="thisDevice.name + '.filter.current'"></indi-value>
    <indi-element :indiId="thisDevice.name + '.filter.target'" inputWidth="5"></indi-element>
    <button @click.prevent="sendHome"><i class="material-icons">home</i>home</button>
    <button @click.prevent="sendStop"><i class="material-icons">block</i>stop</button>

    <indi-switch-multi-element :orientation="orientation" :disabled="isDisabled" :device="thisDevice" :property="filterNames" ></indi-switch-multi-element>
  </div>
</template>
<style lang="scss" scoped>
.filter-wheel {
  margin: 1rem;
  flex: 1;
}
</style>
<script>
import IndiElement from "~/components/indi/IndiElement.vue";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import indi from "~/mixins/indi.js";

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
    IndiValue
  },
  methods: {
    sendHome: function() {
      if (!this.thisDevice) return;
      this.sendIndiNew(this.thisDevice, this.thisDevice.properties["home"], this.thisDevice.properties["home"].elements["request"], "On");
    },
    sendStop: function() {
      if (!this.thisDevice) return;
      this.sendIndiNew(this.thisDevice, this.thisDevice.properties["stop"], this.thisDevice.properties["stop"].elements["request"], "On");
    }
  },
  computed: {
    isDisabled: function () {
      if (!(this.thisDevice && this.thisDevice.properties['fsm'])) { return true; }
      const fsmState = this.thisDevice.properties["fsm"].elements["state"].value;
      return !(fsmState == "READY" || fsmState == "OPERATING") || this.filterNames.state == 'Busy';
    },
    filterNames: function () {
      if (this.thisDevice && this.thisDevice.properties['filterName']) {
        return this.thisDevice.properties['filterName'];
      } else {
        return null;
      }
    },
    name: function () {
      if (this.label) {
        return this.label;
      } else if (this.thisDevice) {
        return this.thisDevice.name;
      } else {
        return this.indiId;
      }
    },
    fsmState: function () {
      if (this.thisDevice && this.thisDevice.properties['fsm']) {
        return this.thisDevice.properties['fsm'].elements['state'].value;
      } else {
        return null;
      }
    }
  }
};
</script>