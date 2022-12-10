import 'regenerator-runtime/runtime'
import Vue from 'vue';
import { DateTime } from "luxon";
import store from "./store";
import App from './App.vue';
import io from 'socket.io-client';
import VueSocketIO from 'vue-socket.io';
import router from "./router.js";
import utils from "./mixins/utils.js";
import VueVirtualScroller from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
Vue.use(VueVirtualScroller)

let buildConnectionString;
if (process.env.NODE_ENV == 'development') {
  buildConnectionString = function() {
    const apiPort = 8000;
    const wsProto = window.location.protocol == "https:" ? "wss:" : "ws:";
    let connectionString = wsProto + '//' + window.location.hostname;
    if (window.location.port) {
      connectionString += ':' + String(apiPort);
    }
    return connectionString;
  }
} else {
  buildConnectionString = function() {
    const wsProto = window.location.protocol == "https:" ? "wss:" : "ws:";
    let connectionString = wsProto + '//' + window.location.hostname;
    if (window.location.port) {
      connectionString += ':' + String(window.location.port);
    }
    return connectionString;
  }

}
Vue.use((Vue) => {
  // Assign a unique id to each component
  let uuid = 0;
  Vue.mixin({
    beforeCreate: function() {
      this.uuid = uuid.toString();
      uuid += 1;
    },
  });

  // Generate a component-scoped id
  Vue.prototype.$id = function(id) {
    return "component-" + this.uuid + "-" + id;
  };
});

// let ws = null;
// let webSocketIsConnected = false;
let reconnectionTimer = null;
let textEncoder = new TextEncoder();
let textDecoder = new TextDecoder();




new Vue({
  store,
  router,
    render: h => h(App),
    methods: {
      updateCurrentTime: function () {
        this.currentTime = DateTime.utc();
        setTimeout(() => { this.updateCurrentTime(); }, 1000);
      },
      sendIndiNewByNames: function (deviceName, propertyName, elementName, value) {
        const payload = {
          'device': deviceName,
          'property': propertyName,
          'element': elementName,
          'value': value
        };
        const payloadText = JSON.stringify({'action': 'indi_new', payload});
        this.ws.send(textEncoder.encode(payloadText));
        console.log('Emitted indi_new', payloadText);
      },
      onWebSocketOpen(event) {
        this.webSocketIsConnected = true;
        this.ws.send(textEncoder.encode(JSON.stringify({hello: "world"})));
      },
      onWebSocketMessage(event) {
        event.data.arrayBuffer().then((buf) => {
          let msg = JSON.parse(textDecoder.decode(buf));
          console.log(msg)
          if (msg.action == "init") {
            this.reinitializeIndiWorld(msg.payload);
            // this.indiWorld = msg.payload;
          } else if (msg.action == "batch_update") {
            this.batchUpdate(msg.payload);
          }
        });
      },
      onWebSocketClose(event) {
        this.webSocketIsConnected = false;
        // this.indiWorld = {};
        this.purgeIndiWorld();
      },
      onWebSocketError(event) {
        console.error(event);
        this.ws.close();
      },
      connectWebSocket() {
        if (this.ws !== null && (this.ws.readyState == WebSocket.CONNECTING || this.ws.readyState == WebSocket.OPEN)) {
          return this.ws;
        }
        const connectionURL = buildConnectionString() + "/websocket";
        console.log("Connecting to", connectionURL)
        let ws = new WebSocket(connectionURL);
        ws.addEventListener('open', this.onWebSocketOpen);
        ws.addEventListener('message', this.onWebSocketMessage);
        ws.addEventListener('close', this.onWebSocketClose);
        ws.addEventListener('error', this.onWebSocketError);
        this.ws = ws;
        return ws;
      },
      initializeIndiWorld: function() {
        this.connectWebSocket();
      },
      purgeIndiWorld: function() {
        for (let deviceName of Object.keys(this.indiWorld)) {
          let device = payload[deviceName]
          for (let propertyName of Object.keys(device)) {
            Vue.delete(this.indiWorld[deviceName][propertyName]);
          }
        }
      },
      reinitializeIndiWorld: function(payload) {
        for (let deviceName of Object.keys(payload)) {
          let device = payload[deviceName]
          for (let propertyName of Object.keys(device)) {
            this.singlePropertyUpdate(deviceName, propertyName, device[propertyName]);
          }
        }
      },
      batchUpdate(payload) {
        const updates = payload.updates;
        const deletions = payload.deletions;
        for (let propSpec of deletions) {
          let [deviceName, propertyName] = propSpec.split(".");
          this.singlePropertyDelete(deviceName, propertyName);
        }
        for (let propSpec of Object.keys(updates)) {
          let [deviceName, propertyName] = propSpec.split(".");
          this.singlePropertyUpdate(deviceName, propertyName, updates[propSpec]);
        }
      },
      singlePropertyDelete(deviceName, propertyName) {
        Vue.delete(this.indiWorld[deviceName], propertyName);
      },
      singlePropertyUpdate(deviceName, propertyName, state) {
        if (!this.indiWorld.hasOwnProperty(deviceName)) {
          Vue.set(this.indiWorld, deviceName, {});
        }
        Vue.set(this.indiWorld[deviceName], propertyName, state);
      },
    },
    data() {
      return {
        currentTime: DateTime.utc(),
        indiWorld: {},
        ws: null,
        webSocketIsConnected: false,
        reconnectionTimer: null,
      };
    },
    mounted() {
      this.updateCurrentTime();
      this.initializeIndiWorld();
      this.reconnectionTimer = setInterval(() => {
        if(this.ws === null || this.ws.readyState == WebSocket.CLOSED || this.ws.readyState == WebSocket.CLOSING ) {
          this.connectWebSocket();
        }
      }, 1000);
      console.log("Set reconnectionTimer", reconnectionTimer);
    },
    beforeUnmount() {
      if (this.reconnectionTimer) {
        clearInterval(this.reconnectionTimer);
      }
    },
    provide: function () {
      const time = {}
      Object.defineProperty(time, 'currentTime', {
         enumerable: true,
         get: () => this.currentTime,
      })
      const indi = {sendIndiNewByNames: this.sendIndiNewByNames};
      Object.defineProperty(indi, 'world', {
         enumerable: true,
         get: () => this.indiWorld,
      })
      return { time, indi }
    }
  }).$mount('#app')

