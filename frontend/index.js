import Vue from 'vue';
import { DateTime } from "luxon";
import App from './App.vue';
// import router from "./router.js";
import common from "./common.js";
import constants from "./constants.js";
import store from './store';
import { MagAOX_routes, SCOOB_routes } from './routes.js'

import VueRouter from 'vue-router'

Vue.use(VueRouter)

async function fetchConfigData() {
  try {
    const destURL = `${constants.CONFIG_URL}`;
    const res = await fetch(destURL);
    if (!res.ok) {
      console.log("not ok");
      const message = `An error has occured: ${res.status} - ${res.statusText}`;
      console.error(message);
    }
    const data = res.json();
    console.log("Server responded with config data.");
    return data;
  } catch (err) {
    console.error("Error fetching config data:", err);
  }
}


async function initApp() {
  const configData = await fetchConfigData();
  var routes = MagAOX_routes;

  if (configData) {
    if (configData.layout === constants.SCOOB){
      routes = SCOOB_routes;
    } else if (configData.layout === constants.MAGAOX) {
      routes = MagAOX_routes;
    }
    store.dispatch('fetchConfig', configData);
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
