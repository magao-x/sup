import Vue from 'vue';
import VueRouter from 'vue-router'

Vue.use(VueRouter)

import store from '~/store';
import PropertiesTable from "~/pages/PropertiesTable.vue";
import KitchenSink from "~/pages/KitchenSink.vue";
import Dashboard from "~/pages/Dashboard.vue";
import Controls from "~/pages/Controls.vue";

const routes = [
    { path: '/', component: Controls},
    { path: '/properties', component: PropertiesTable },
    { path: '/kitchensink', component: KitchenSink },
    { path: '/dashboard', component: Dashboard }
];
export default new VueRouter({
    routes
})