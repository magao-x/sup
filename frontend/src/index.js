import { createApp } from 'vue';
import { DateTime } from "luxon";
import App from './App.vue';
import common from "./common.js";
import constants from "./constants.js";
import store from './store';
import { map } from './map.js'
import utils from './utils.js';
import { createRouter, createWebHistory } from 'vue-router'

import '@/css/main.scss';

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

  // const router = new VueRouter({
  //   routes
  // });

  const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
  })

  const app = createApp({
    router,
    store,
    mixins: [common],
    render: h => h(App),
  });
  app.use(router);
  app.use(store);
  app.mount('#app');
}

initApp();
