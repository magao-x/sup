<template>
  <div>
    <!-- {{ indi }} -->
    <div v-for="dev in devices" :key="dev.name">
      <!-- {{ devName }} -->
      <indi-device :device="dev" @deviceChange="deviceChange" />
    </div>
  </div>
</template>

<script>
import Vue from "vue";
import io from 'socket.io-client';
import IndiDevice from "./IndiDevice.vue";

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
  }
});
</script>

<style lang="scss" scoped>
.container {
  color: green;
}
</style>
