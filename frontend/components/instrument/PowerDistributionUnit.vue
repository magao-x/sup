<template>
  <div v-if="thisDevice" class="pdu">
    <div class="pdu-row">
      <div class="pdu-label">
        {{ thisDevice.name }}
      </div>
      <div class="pdu-channel" v-for="channel in channels" :key="channel.name">
        <div class="channel-name">{{ channel.name }}</div>
        <div class="channel-controls">
          <power-toggle :device="thisDevice" :property="channel" :disabled="disabled"></power-toggle>
        </div>
      </div>
    </div>
  </div>
  <div v-else>
    Waiting for device {{ device }}
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.pdu {
  .pdu-row {
    display: flex;
    flex-direction: row;
    margin-bottom: $unit;
    .pdu-label {
      writing-mode: vertical-lr;
      text-align: center;
      padding-right: $unit;
      border-right: 1px solid $primary;
    }
    .pdu-channel {
      flex: 1;
      max-width: 6em;
      display: flex;
      flex-direction: column;
      color: $base2;
      .channel-name, .channel-controls {
        flex: 1;
      }
      border-bottom: 1px solid $primary;
      padding-left: $unit;
      padding-bottom: $unit;
    }
  }
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiProperty from "~/components/indi/IndiProperty.vue";
import PowerToggle from "~/components/instrument/PowerToggle.vue";

export default {
  props: ["device", "indiId", "disabled"],
  mixins: [indi, utils],
  components: {
    IndiProperty,
    PowerToggle
  },
  computed: {
    channels: function() {
      const channelKeys = Object.keys(this.thisDevice.properties["channelOutlets"].elements);
      const propertyKeys = Object.keys(this.thisDevice.properties);
      const channels = propertyKeys.filter(prop => channelKeys.includes(prop));
      return channels.map(key => this.thisDevice.properties[key]);
    }
  }
};
</script>