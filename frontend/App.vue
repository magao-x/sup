<template>
  <div>
    <!-- {{ indi }} -->
    <div v-for="(dev, devName) in devices">
      <!-- {{ devName }} -->
      <div v-for="(prop, propName) in dev">
        <!-- {{ propName }} -->
        <div v-for="(elem, elemName) in prop">
          <div v-if="elemName[0] !== '_'">{{ devName }}.{{ propName }}.{{ elemName }}={{ elem.value }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from "vue";
import io from 'socket.io-client';

export default Vue.extend({
  data() {
    return {
      updates: ""
    };
  },
  computed: {
    count () {
      return this.$store.state.count
    },
    devices() { return this.$store.state.devices }
  }
});
</script>

<style lang="scss" scoped>
.container {
  color: green;
}
</style>
