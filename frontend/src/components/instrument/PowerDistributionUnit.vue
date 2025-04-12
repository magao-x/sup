<template>
    <div v-if="thisDevice" :class="classes">
      <div class="pdu-label">
        {{ thisDeviceName }}
      </div>
      <div class="pdu-channel" v-for="channel in channels" :key="channel.name">
        <div class="channel-name">{{ channel.name }}</div>
        <div class="channel-controls">
          <power-toggle :device="thisDevice" :property="channel" :disabled="disabled"></power-toggle>
        </div>
      </div>
    </div>  
    <div v-else :class="classes">
      <div class="pdu-label">
        {{ indiId }}
      </div>
      <div class="pdu-channel">
        <div class="channel-name"></div>
        <div class="channel-controls">
          Waiting for device {{ indiId }}
        </div>
      </div>
    </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

  .pdu {
    display: flex;
    flex-direction: row;
    margin: 0 $unit calc($unit / 2) $unit;
    .pdu-label {
      writing-mode: vertical-lr;
      text-align: center;
      padding-right: $unit;
      border-right: 1px solid $plasma-blue;
    }
    .pdu-channel {
      flex: 1;
      max-width: 7em;
      display: flex;
      flex-direction: column;
      color: var(--fg-normal);
      border-bottom: 1px solid $plasma-blue;
      padding-left: $medgap;
      padding-bottom: $medgap;
      .channel-name, .channel-controls {
        flex: 1;
        margin-bottom: $medgap;
      }
    }
    &.disabled {
      .pdu-channel {
        max-width: inherit;
      }
    }
    &.usbdu {
      .pdu-label {
        border-right: 1px solid $sunbeam-yellow;
      }
      .pdu-channel {
        border-bottom: 1px solid $sunbeam-yellow;
      }
    }
    &.dcdu {
      .pdu-label {
        border-right: 1px solid $noble-fir;
      }
      .pdu-channel {
        border-bottom: 1px solid $noble-fir;
      }
    }
  }

</style>
<script>
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";
import IndiProperty from "@/components/indi/IndiProperty.vue";
import PowerToggle from "@/components/instrument/PowerToggle.vue";

export default {
  props: ["device", "indiId", "disabled"],
  mixins: [indi, utils],
  components: {
    IndiProperty,
    PowerToggle
  },
  computed: {
    classes: function() {
      let elemClasses = ["pdu"];
      elemClasses.push(this.indiId.replace(/\d+/g, ''));
      if (this.thisDevice === null) {
        elemClasses.push("disabled");
      }
      return elemClasses;
    },
    channels: function() {
      if (this.thisDevice === null) {
        return [];
      }
      const channelKeys = Object.keys(this.thisDevice["channelOutlets"]._elements);
      const propertyKeys = Object.keys(this.thisDevice);
      const channels = propertyKeys.filter(prop => channelKeys.includes(prop)).sort();
      return channels.map(key => this.thisDevice[key]);
    }
  }
};
</script>
