import Vue from 'vue';
import { DateTime } from "luxon";
import App from './App.vue';
// import router from "./router.js";
import common from "./common.js";
import constants from "./constants.js";
import store from './store';
import { map } from './map.js'
import utils from '~/utils.js';
import VueRouter from 'vue-router'

Vue.use(VueRouter)

async function fetchConfigData() {
  try {
    const destURL = utils.buildBackendUrl('config');
    const res = await fetch(destURL);
    if (!res.ok) {
      console.log("not ok");
      const message = `An error has occured: ${res.status} - ${res.statusText}`;
      console.error(message);
    }
    const data = res.json();
    return data;
  } catch (err) {
    console.error("Error fetching config data:", err);
  }
}

async function initApp() {
  const configData = await fetchConfigData();
  console.log("Server responded with config:", configData);
  store.dispatch('fetchConfig', configData);

  var routes = [];

  if (map[configData.layout] && map[configData.layout]['routes']) {
    var routes = map[configData.layout]['routes'];
  }

  const router = new VueRouter({
    routes
  });

  new Vue({
    router,
    store,
    mixins: [common],
    render: h => h(App),
  }).$mount('#app');
}

initApp();
