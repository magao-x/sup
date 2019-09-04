import Vue from 'vue';
import Vuex from 'vuex'

Vue.use(Vuex)

import App from './App.vue';
import io from 'socket.io-client';
import VueSocketIO from 'vue-socket.io';

const store = new Vuex.Store({
    state: {
      count: 0,
      devices: {}
    },
    mutations: {
      increment (state) {
        state.count++
      },
      indi_init(state, payload) {
        state.devices = payload;
        console.log('indi_init mutation end')
      },
      indi_def(state, payload) {
        const deviceName = payload.device;
        const propertyName = payload.name;
        if (typeof state.devices[deviceName] === "undefined") {
          // create device entry if necessary
          console.log("Creating device", deviceName);
          Vue.set(state.devices, deviceName, {});
        }
        Vue.set(state.devices[deviceName], propertyName, payload.property);
        // state.devices[deviceName][propertyName] = payload.property;
        console.log('indi_def end, assigned to', deviceName, propertyName);
      },
      indi_set(state, payload) {
        console.log('started indi_set');
        const deviceName = payload.device;
        const propertyName = payload.name;
        const elements = payload.property.elements;

        let currentElements = Object.keys(state.devices[deviceName][propertyName].elements);
        for(let el of currentElements) {
          let theElem = state.devices[deviceName][propertyName].elements[el];
          const matchElem = elements[el];
          if (typeof matchElem !== "undefined") {
            console.log("Updating", theElem.name, 'to', matchElem.value);
            theElem.value = matchElem.value;
          }
        }
      },
      indi_del(state, payload) {
        const deviceName = payload.device;
        if ('name' in payload) {
          Vue.delete(state.devices[deviceName], payload.name);
        } else {
          Vue.delete(state.devices, deviceName);
        }
      }
    },
    actions: {
        srv_indi_init({ commit }, payload) {
          console.log('init', payload);
          commit('indi_init', payload);
        },
        srv_indi_def({ commit }, payload) {
          console.log('def', payload);
          commit('indi_def', payload);
        },
        srv_indi_set({ commit }, payload) {
          console.log('set', payload);
          commit('indi_set', payload);
        },
        srv_indi_del({ commit }, payload) {
          console.log('del', payload);
          commit('indi_del', payload);
        }
    }
  });

Vue.use(new VueSocketIO({
    debug: true,
    connection: io(),
    vuex: {
        store,
        actionPrefix: 'srv_'
    }
}));

new Vue({
    store,
    render: h => h(App)
  }).$mount('#app')

