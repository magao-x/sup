import Vue from 'vue';
import Vuex from 'vuex';
import { DateTime } from "luxon";

Vue.use(Vuex)

export default new Vuex.Store({
    state: {
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
    },
    mutations: {
      heartbeat (state) {
        state.webSocketConnection.connected = true;
        state.webSocketConnection.lastUpdate = DateTime.utc();
      },
      disconnected (state) {
        state.webSocketConnection.connected = false;
        state.indiConnection.connected = false;
      },
      
      updateTime (state, payload) {
        const { localSiderealTime, UTC } = payload;
        state.localSiderealTime = localSiderealTime;
        state.UTC = UTC;
      },
      indi_connect(state){
        state.indiConnection.connected = true;
        state.indiConnection.lastUpdate = DateTime.utc();
      },
      indi_disconnect(state){
        state.indiConnection.connected = false;
      },
      indi_init(state, payload) {
        Vue.set(state, "devices", payload);
      },
      indi_update(state, payload) {
        let {deviceName, propertyName, propertyState} = payload;
        if (typeof state.devices[deviceName] === "undefined") {
          // create device entry if necessary
          Vue.set(state.devices, deviceName, {
            "name": deviceName,
            "properties": {}
          });
        }
        if (typeof state.devices[deviceName].properties[propertyName] === "undefined") {
          // create device entry if necessary
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
        commit('indi_init', payload);
      },
      srv_indi_batch_update({ commit }, payload) {
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
        const localSiderealTime = payload.localSiderealTime;
        const UTC = payload.UTC;
        for (let propSpec of deletions) {
          let [deviceName, propertyName] = propSpec.split(".");
          commit('indi_del', {deviceName, propertyName});
        }
        for (let propSpec of Object.keys(updates)) {
          let [deviceName, propertyName] = propSpec.split(".");
          commit('indi_update', {deviceName, propertyName, propertyState: updates[propSpec]});
        }
        commit('heartbeat');
        commit('updateTime', {localSiderealTime, UTC: payload.UTC});
        if (payload.connected) {
          commit('indi_connect');
        } else {
          commit('indi_disconnect');
        }
      }
    }
  });
