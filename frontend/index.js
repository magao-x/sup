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
        state.devices = payload;
        console.log('indi_init mutation end')
      },
      // indi_batch_update(state, payload) {

      // },
      indi_def(state, payload) {
        const deviceName = payload.device;
        const propertyName = payload.property.name;
        if (typeof state.devices[deviceName] === "undefined") {
          // create device entry if necessary
          console.log("Creating device", deviceName);
          Vue.set(state.devices, deviceName, {
            "name": deviceName,
            "properties": {}
          });
        }
        Vue.set(state.devices[deviceName].properties, propertyName, payload.property);
        console.log("payload.property = ", payload.property);
        // state.devices[deviceName][propertyName] = payload.property;
        console.log('indi_def end, assigned to', deviceName, propertyName);
        console.log('state.devices[deviceName].properties[propertyName] =', state.devices[deviceName].properties[propertyName]);
      },
      indi_set(state, payload) {
        console.log('started indi_set');
        const deviceName = payload.device;
        if (state.devices[deviceName] === undefined) {
          return;
        }
        const propertyName = payload.property.name;
        const elements = payload.property.elements;
        const propertyKeysToUpdate = Object.keys(payload.property).filter(
          (name) => (
            name != 'name' &&
            name != 'elements' &&
            payload.property[name] !== undefined
          )
        ).map(function (key) {
          Vue.set(state.devices[deviceName].properties[propertyName], key, payload.property[key]);
        });

        let currentElements = Object.keys(state.devices[deviceName].properties[propertyName].elements);
        for(let el of currentElements) {
          let theElem = state.devices[deviceName].properties[propertyName].elements[el];
          const matchElem = elements[el];
          if (typeof matchElem !== "undefined") {
            console.log("Updating", theElem.name, '=', theElem.value, 'to', matchElem.value);
            theElem.value = matchElem.value;
          }
        }
      },
      indi_del(state, payload) {
        const deviceName = payload.device;
        if ('name' in payload) {
          Vue.delete(state.devices[deviceName].properties, payload.name);
        } else {
          Vue.delete(state.devices, deviceName);
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
          const updates = payload.indi_updates;
          for (let update of updates) {
            if (update['action'] === 'def') {
              commit('indi_def', update);
            } else if (update['action'] === 'set') {
              commit('indi_set', update);
            } else if (update['action'] === 'del') {
              commit('indi_del', update);
            }
          }
          commit('heartbeat');
        },
        // srv_indi_def({ commit }, payload) {
        //   console.log('def', payload);
        //   commit('indi_def', payload);
        // },
        // srv_indi_set({ commit }, payload) {
        //   console.log('set', payload);
        //   commit('indi_set', payload);
        // },
        // srv_indi_del({ commit }, payload) {
        //   console.log('del', payload);
        //   commit('indi_del', payload);
        // }
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

