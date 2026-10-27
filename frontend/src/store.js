import Vue from 'vue';
import { createStore } from 'vuex'
import { DateTime } from "luxon";
import constants from "./constants.js";

const AUDIBLE_ALERTS_STORAGE_KEY = "sup.audibleAlerts";
const DEFAULT_ALERT_VOLUME = 0.8;

function loadAudibleAlertsPreferences() {
  // Both the opt-in and the volume persist, so someone who turned alerts on
  // does not have to turn them on again after every reload. Whether the
  // browser will actually *play* anything is a separate question --- see
  // restoreSession() in audibleAlerts.js --- and it is answered at startup
  // rather than assumed here. Anything unreadable or unrecognized reads as
  // off, so a corrupt value can never switch alerts on by accident.
  const preferences = { enabled: false, volume: DEFAULT_ALERT_VOLUME, blocked: false };
  try {
    const stored = window.localStorage.getItem(AUDIBLE_ALERTS_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      preferences.enabled = parsed.enabled === true;
      if (typeof parsed.volume === "number" && parsed.volume >= 0 && parsed.volume <= 1) {
        preferences.volume = parsed.volume;
      }
    }
  } catch (err) {
    console.warn("Could not read saved audible alert preferences", err);
  }
  return preferences;
}

function saveAudibleAlertsPreferences(state) {
  try {
    window.localStorage.setItem(
      AUDIBLE_ALERTS_STORAGE_KEY,
      JSON.stringify({ enabled: state.enabled, volume: state.volume })
    );
  } catch (err) {
    console.warn("Could not save audible alert preferences", err);
  }
}

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
      instGraphRev: null,
      audibleAlerts: loadAudibleAlertsPreferences(),
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
    setAudibleAlertsEnabled(state, enabled) {
      state.audibleAlerts.enabled = enabled;
      saveAudibleAlertsPreferences(state.audibleAlerts);
    },
    setAudibleAlertsVolume(state, volume) {
      const parsed = parseFloat(volume);
      if (Number.isNaN(parsed)) {
        return;
      }
      state.audibleAlerts.volume = Math.min(1, Math.max(0, parsed));
      saveAudibleAlertsPreferences(state.audibleAlerts);
    },
    setAudibleAlertsBlocked(state, blocked) {
      state.audibleAlerts.blocked = blocked;
    },
    setInstGraph(state, payload) {
      state.instGraphUpdateTime = Date.now();
      state.instGraphFilename = payload.file;
      state.instGraphRev = payload.rev;
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
    updateInstGraph({ commit }, payload) {
      commit('setInstGraph', payload);
    }
  }
});
