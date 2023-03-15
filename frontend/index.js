import Vue from 'vue';
import { DateTime } from "luxon";
import App from './App.vue';
import router from "./router.js";
import common from "./common.js";

new Vue({
  router,
  mixins: [common],
  render: h => h(App),
}).$mount('#app')

