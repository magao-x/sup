import Vue from 'vue';
import Vuex from 'vuex'
import { DateTime } from "luxon";

Vue.use(Vuex)

import App from './App.vue';
import io from 'socket.io-client';
import VueSocketIO from 'vue-socket.io';

const store = new Vuex.Store({
    state: {
      connection: {
        connected: false,
        lastUpdate: null
      },
      devices: {}
    },
    mutations: {
      heartbeat (state) {
        state.connection.connected = true;
        state.connection.lastUpdate = DateTime.utc();
      },
      disconnected (state) {
        state.connection.connected = false;
      },
      indi_init(state, payload) {
        Vue.set(state, "devices", payload);
        console.log('indi_init mutation end')
      },
      indi_update(state, payload) {
        let {deviceName, propertyName, propertyState} = payload;
        if (typeof state.devices[deviceName] === "undefined") {
          // create device entry if necessary
          console.log("Creating device", deviceName);
          Vue.set(state.devices, deviceName, {
            "name": deviceName,
            "properties": {}
          });
        }
        if (typeof state.devices[deviceName].properties[propertyName] === "undefined") {
          // create device entry if necessary
          console.log("Creating property", propertyName);
          Vue.set(state.devices[deviceName].properties, propertyName, propertyState);
        } else {
          state.devices[deviceName].properties[propertyName] = propertyState;
        }
        
      },
      indi_del(state, payload) {
        let {deviceName, propertyName} = payload;
        if (propertyName === "*") {
          Vue.delete(state.devices, deviceName);
        } else {
          Vue.delete(state.devices[deviceName].properties, propertyName);
        }
      }
    },
    actions: {
      srv_heartbeat({ commit }, payload) {
        commit('heartbeat');
      },
      srv_disconnected({ commit }, payload) {
        commit('disconnected');
      },
      srv_indi_init({ commit }, payload) {
        console.log('init', payload);
        commit('indi_init', payload);
      },
      srv_indi_batch_update({ commit }, payload) {
        console.log('batch_update', payload);
        // const updates = payload.indi_updates;
        // for (let update of updates) {
        //   if (update['action'] === 'def') {
        //     commit('indi_def', update);
        //   } else if (update['action'] === 'set') {
        //     commit('indi_set', update);
        //   } else if (update['action'] === 'del') {
        //     commit('indi_del', update);
        //   }
        // }
        const updates = payload.updates;
        const deletions = payload.deletions;
        for (let propSpec of deletions) {
          let [deviceName, propertyName] = propSpec.split(".");
          commit('indi_del', {deviceName, propertyName});
        }
        for (let propSpec of Object.keys(updates)) {
          let [deviceName, propertyName] = propSpec.split(".");
          commit('indi_update', {deviceName, propertyName, propertyState: updates[propSpec]});
        }
        commit('heartbeat');
      }
    }
  });

const socket = io("http://localhost:8000");
for (let evt of ['pong', 'connect']) {
  socket.on(evt, () => {store.commit('heartbeat'); console.log('Heart beat')});
}
for (let evt of ['connect_error', 'connect_timeout', 'disconnect']) {
  socket.on(evt, () => store.commit('disconnected'));
}

socket.on('connect_error', (err) => console.error("socket.io connection error", err));

Vue.use(new VueSocketIO({
    debug: true,
    connection: socket,
    vuex: {
        store,
        actionPrefix: 'srv_'
    }
}));

new Vue({
    store,
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
      // return {currentTime: this.currentTime};
      const time = {}
      Object.defineProperty(time, 'currentTime', {
         enumerable: true,
         get: () => this.currentTime,
      })
      return { time }
    }
  }).$mount('#app')

