import Vue from 'vue';
import { DateTime } from "luxon";
import store from "./store";
import App from './App.vue';
import io from 'socket.io-client';
import VueSocketIO from 'vue-socket.io';
import router from "./router.js";
import utils from "./mixins/utils.js";
import VueVirtualScroller from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
Vue.use(VueVirtualScroller)


function buildConnectionString() {
  const apiPort = 8000;
  const connectionString = window.location.protocol + '//' + window.location.hostname + ':' + String(apiPort);
  return connectionString;
}

const socket = io(process.env.NODE_ENV == 'development' ? buildConnectionString() : null);
for (let evt of ['pong', 'connect']) {
  socket.on(evt, () => {store.commit('heartbeat');});
}
for (let evt of ['connect_error', 'connect_timeout', 'disconnect']) {
  socket.on(evt, () => store.commit('disconnected'));
}

socket.on('connect_error', (err) => console.error("socket.io connection error", err));

Vue.use(new VueSocketIO({
    debug: false, // process.env.NODE_ENV == 'development',
    connection: socket,
    vuex: {
        store,
        actionPrefix: 'srv_'
    }
}));

Vue.use((Vue) => {
  // Assign a unique id to each component
  let uuid = 0;
  Vue.mixin({
    beforeCreate: function() {
      this.uuid = uuid.toString();
      uuid += 1;
    },
  });

  // Generate a component-scoped id
  Vue.prototype.$id = function(id) {
    return "component-" + this.uuid + "-" + id;
  };
});

new Vue({
    store,
    router,
    render: h => h(App),
    methods: {
      updateCurrentTime: function () {
        this.currentTime = DateTime.utc();
        setTimeout(() => { this.updateCurrentTime(); }, 1000);
      }
    },
    data() {
      return {
        currentTime: DateTime.utc()
      };
    },
    mounted() {
      this.updateCurrentTime();
    },
    provide: function () {
      const time = {}
      Object.defineProperty(time, 'currentTime', {
         enumerable: true,
         get: () => this.currentTime,
      })
      return { time }
    }
  }).$mount('#app')

