import Vue from 'vue';
import { DateTime } from "luxon";
import VueVirtualScroller from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import .constants from "./constants.js";

Vue.use(VueVirtualScroller)

import VueAxios from './mixins/axios.js'
import { MagAOX_routes, SCOOB_routes } from './routes.js'
import constants from './constants.js';
Vue.use(VueAxios)

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


let textEncoder = new TextEncoder();
let textDecoder = new TextDecoder();

const MAX_LOG_ENTRIES = 1000;

export default {
    methods: {
        updateCurrentTime: function () {
          this.currentTime = DateTime.utc();
          setTimeout(() => { this.updateCurrentTime(); }, 1000);
        },
        sendIndiNewByNames: function (deviceName, propertyName, elementName, value) {
          if (value === null) {
            return;
          }
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
          console.log("Connected to WebSocket");
        },
        onWebSocketMessage(event) {
          event.data.arrayBuffer().then((buf) => {
            let msg = JSON.parse(textDecoder.decode(buf));
            if (msg.action == "init") {
              this.reinitializeIndiWorld(msg.payload);
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
            Vue.delete(this.indiWorld, deviceName);
          }
        },
        reinitializeIndiWorld: function(payload) {
          for (let deviceName of Object.keys(payload)) {
            let device = payload[deviceName]
            for (let propertyName of Object.keys(device)) {
              this.singlePropertyUpdate(deviceName, propertyName, device[propertyName]);
            }
          }
          this.lastUpdate = DateTime.utc();
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
          this.lastUpdate = DateTime.utc();
          this.indiIsConnected = payload.connected;
          this.systemLogs = this.systemLogs.concat(payload.logs);
          if (this.systemLogs.length > MAX_LOG_ENTRIES) {
            this.systemLogs.splice(0, this.systemLogs.length - MAX_LOG_ENTRIES);
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
        fetchRoutes() {
          this.$axios.get(constants.CONFIG_URL)
            .then(response => {
              this.updateConfig(response.data);
              console.log("Axios responded with config data.");
              if (response.data.layout === 'SCOOB'){
                SCOOB_routes.forEach((route) => {
                  this.$router.addRoute({path: route.path, component: route.component})
                });   
              } else {        
                MagAOX_routes.forEach((route) => {
                  this.$router.addRoute({path: route.path, component: route.component})
                });                  
              }
            })
            .catch(error => {
              console.error('Error fetching routes:', error);
            });
        },
        updateConfig(new_config) {
          for (const [key, value] of Object.entries(new_config)) {
            if (key in this.config) {
              this.config[key] = value;
            }
          }
        },   
      },
      data() {
        return {
          currentTime: DateTime.utc(),
          indiWorld: {},
          systemLogs: [],
          ws: null,
          webSocketIsConnected: false,
          indiIsConnected: false,
          lastUpdate: null,
          reconnectionTimer: null,
          config: {"layout": constants.DEFAULT_LAYOUT},
        };
      },
      mounted() {
        this.fetchRoutes();        
        this.updateCurrentTime();
        this.initializeIndiWorld();
        this.reconnectionTimer = setInterval(() => {
          if(this.ws === null || this.ws.readyState == WebSocket.CLOSED || this.ws.readyState == WebSocket.CLOSING ) {
            this.connectWebSocket();
          }
        }, 1000);
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
        const indi = {
          sendIndiNewByNames: this.sendIndiNewByNames,
        };
        Object.defineProperty(indi, 'world', {
           enumerable: true,
           get: () => this.indiWorld,
        })
        Object.defineProperty(indi, 'logs', {
          enumerable: true,
          get: () => this.systemLogs,
       })
        Object.defineProperty(indi, 'lastUpdate', {
          enumerable: true,
          get: () => this.lastUpdate,
        })
        Object.defineProperty(indi, 'webSocketIsConnected', {
          enumerable: true,
          get: () => this.webSocketIsConnected,
        })
        Object.defineProperty(indi, 'indiIsConnected', {
          enumerable: true,
          get: () => this.indiIsConnected,
        })
        const config = this.config
        Object.defineProperty(config, 'config', {
           enumerable: true,
           get: () => this.config,
        })        
        return { time, indi, config }
      }
  }