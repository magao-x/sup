<template>
  <div>
    <!-- {{ indi }} -->
    <div v-for="(dev, devName) in devices" :key="devName">
      <!-- {{ devName }} -->
      <indi-device :name="devName" :device="dev" @deviceChange="deviceChange" />
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
    deviceChange: function (e) {
      console.log("Device change:", e);
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
