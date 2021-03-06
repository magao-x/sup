import Vue from 'vue';
import VueRouter from 'vue-router'

Vue.use(VueRouter)

import store from '~/store';
import PropertiesTable from "~/pages/PropertiesTable.vue";
import VirtualMachine from "~/pages/VirtualMachine.vue";
import LabMode from "~/pages/LabMode.vue";
import Dashboard from "~/pages/Dashboard.vue";
import Cameras from "~/pages/Cameras.vue";
import AdaptiveOptics from "~/pages/AdaptiveOptics.vue";
import Power from "~/pages/Power.vue";

const routes = [
    { path: '/', component: Cameras},
    { path: '/ao', component: AdaptiveOptics},
    { path: '/power', component: Power},
    { path: '/properties', component: PropertiesTable },
    { path: '/vm', component: VirtualMachine },
    { path: '/lab', component: LabMode },
    { path: '/dashboard', component: Dashboard }
];
export default new VueRouter({
    routes
})