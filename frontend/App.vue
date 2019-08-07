<template>
  <div>Howdy</div>
</template>

<script>
import Vue from "vue";
import io from 'socket.io-client';

export default Vue.extend({
  sockets: {
    connect: function () {
        console.log('socket connected')
    }
  },
  data() {
    return {
      bundler: "Parcel"
    };
  }
});
</script>

<style lang="scss" scoped>
.container {
  color: green;
}
</style>
