<template>
  <div>
    <!-- {{ indi }} -->
    <div class="device" v-for="dev in objectAsSortedArray(devices)" :key="dev.name">
      <!-- {{ devName }} -->
      <indi-device :device="dev"></indi-device>
    </div>
  </div>
</template>

<script>
import Vue from "vue";
import io from 'socket.io-client';
import IndiDevice from "./IndiDevice.vue";
import utils from "./utils.js";

export default Vue.extend({
  components: {
    IndiDevice
  },
  methods: {
    deviceChange: function (payload) {
      console.log("Device change:", payload);
      this.$socket.emit('indi_new', payload);
    }
  },
  data() {
    return {
      updates: ""
    };
  },
  computed: {
    count () {
      return this.$store.state.count
    },
    devices() {
      return this.$store.state.devices
    }
  },
  mixins: [utils]
});
</script>

<style lang="scss" scoped>
.device {
  border: 1px solid #EE6F31;
  padding: 1rem;
}
</style>
