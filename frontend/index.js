import Vue from 'vue';
import App from './App.vue';
import io from 'socket.io-client';
import VueSocketIO from 'vue-socket.io';
Vue.use(new VueSocketIO({
    debug: true,
    connection: io()
}));

new Vue(App).$mount('#app')
