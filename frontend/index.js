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
    },
    actions: {
        srv_indi_init({ commit }, payload) {
          console.log('init', payload);
          commit('indi_init', payload);
        },
        srv_indi_def({ commit }, payload) {
          console.log('def', payload);
          commit('increment');
        },
        srv_indi_set({ commit }, payload) {
          console.log('set', payload);
          commit('increment');
        },
        srv_indi_new({ commit }, payload) {
          console.log('new', payload);
          commit('increment');
        },
        srv_indi_del({ commit }, payload) {
          console.log('del', payload);
          commit('increment');
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

