import Vue from 'vue';
import { createStore } from 'vuex'
import { DateTime } from "luxon";
import constants from "./constants.js";

export default createStore({
  state() {
    return {
      webSocketConnection: {
        connected: false,
        lastUpdate: null
      },
      indiConnection: {
        connected: false,
        lastUpdate: null
      },
      devices: {},
      localSiderealTime: null,
      UTC: null,
      lightPath: null,
      config: constants.DEFAULT_CONFIG,
      instGraphUpdateTime: null,
      instGraphFilename: null,
    }
  },
  mutations: {
    heartbeat(state) {
      state.webSocketConnection.connected = true;
      state.webSocketConnection.lastUpdate = DateTime.utc();
    },
    disconnected(state) {
      state.webSocketConnection.connected = false;
      state.indiConnection.connected = false;
    },
    updateTime(state, payload) {
      const { localSiderealTime, UTC } = payload;
      state.localSiderealTime = localSiderealTime;
      state.UTC = UTC;
    },
    indi_connect(state) {
      state.indiConnection.connected = true;
      state.indiConnection.lastUpdate = DateTime.utc();
    },
    indi_disconnect(state) {
      state.indiConnection.connected = false;
    },
    indi_init(state, payload) {
      console.log("Inited INDI state", payload);
      Vue.set(state, "devices", payload);
    },
    indi_update(state, payload) {
      let { deviceName, propertyName, propertyState } = payload;
      if (typeof state.devices[deviceName] === "undefined") {
        // create device entry if necessary
        Vue.set(state.devices, deviceName, {});
      }
      if (typeof state.devices[deviceName][propertyName] === "undefined") {
        // create device entry if necessary
        Vue.set(state.devices[deviceName], propertyName, propertyState);
      } else {
        state.devices[deviceName][propertyName] = propertyState;
      }

    },
    indi_del(state, payload) {
      let { deviceName, propertyName } = payload;
      console.log('indi_del', payload);
      if (propertyName === "*") {
        console.log('before delete', state.devices[deviceName]);
        Vue.delete(state.devices, deviceName);
      } else {
        console.log('before delete', state.devices[deviceName][propertyName]);
        Vue.delete(state.devices[deviceName], propertyName);
        console.log('after delete', state.devices[deviceName]);
      }
    },
    setConfig(state, new_config) {
      state.config = new_config;
    },
    setInstGraphUpdateTime(state) {
      state.instGraphUpdateTime = Date.now();
    },
    setInstGraphFilename(state, filename) {
      console.log("Setting instGraph filename",filename)
      state.instGraphFilename = filename;
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
      commit('indi_init', payload);
    },
    srv_indi_batch_update({ commit }, payload) {
      const updates = payload.updates;
      const deletions = payload.deletions;
      const localSiderealTime = payload.localSiderealTime;
      const UTC = payload.UTC;
      for (let propSpec of deletions) {
        let [deviceName, propertyName] = propSpec.split(".");
        commit('indi_del', { deviceName, propertyName });
      }
      for (let propSpec of Object.keys(updates)) {
        let [deviceName, propertyName] = propSpec.split(".");
        commit('indi_update', { deviceName, propertyName, propertyState: updates[propSpec] });
      }
      commit('heartbeat');
      commit('updateTime', { localSiderealTime, UTC: payload.UTC });
      if (payload.connected) {
        commit('indi_connect');
      } else {
        commit('indi_disconnect');
      }
    },
    fetchConfig({ commit }, config) {
      commit('setConfig', config);
    },
    updateInstGraphUpdateTime({ commit }) {
      commit('setInstGraphUpdateTime');
    },
    updateInstGraphFilename({ commit }, filename) {
      commit('setInstGraphFilename', filename);
    }
  }
});
