<template>
  <div v-if="thisDevice" class="pdu">
    <div class="pdu-row">
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
.pdu {
  .pdu-row {
    display: flex;
    flex-direction: row;
    .pdu-channel {
      flex: 1;
      max-width: 6em;
      display: flex;
      flex-direction: column;
      .channel-name, .channel-controls {
        flex: 1;
      }
    }
  }
}
</style>
<script>
import indi from "~/mixins/indi.js";
import IndiProperty from "~/components/indi/IndiProperty.vue";
import PowerToggle from "~/components/instrument/PowerToggle.vue";

export default {
  props: ["device", "indiId", "disabled"],
  mixins: [indi],
  components: {
    IndiProperty,
    PowerToggle
  },
  computed: {
    channels: function() {
      // if (!this.thisDevice) return [];
      const channelKeys = Object.keys(this.thisDevice.properties["channelOutlets"].elements);
      console.log(channelKeys)
      const propertyKeys = Object.keys(this.thisDevice.properties);
      const channels = propertyKeys.filter(prop => channelKeys.includes(prop));
      return channels.map(key => this.thisDevice.properties[key]);
    }
  }
};
</script>