<template>
  <div>{{updates}}</div>
</template>

<script>
import Vue from "vue";
import io from 'socket.io-client';

export default Vue.extend({
  sockets: {
    connect: function () {
        console.log('socket connected')
    },
    indi_update: function (d) {
      console.log(d);
      this.updates += JSON.stringify(d);
    }
  },
  data() {
    return {
      updates: ""
    };
  }
});
</script>

<style lang="scss" scoped>
.container {
  color: green;
}
</style>
