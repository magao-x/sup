import Vue from 'vue';
import { DateTime } from "luxon";
import utils from '@/utils.js';

// Vue.use(VueVirtualScroller)

let textEncoder = new TextEncoder();
let textDecoder = new TextDecoder();

const MAX_LOG_ENTRIES = 10;

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
            } else if (msg.action == "instgraph_updated") {
              console.log("Receiving instGraph data", msg.payload.file);
              this.$store.dispatch('updateInstGraphUpdateTime');
              this.$store.dispatch('updateInstGraphFilename', msg.payload.file);
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
          const connectionURL = utils.buildWebSocketUrl('websocket');
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
        instgraphUpdate(payload) {
          console.log("instGraph updated ", msg.payload.file);
          this.$store.dispatch('updateInstGraphUpdateTime');
          this.$store.dispatch('updateInstGraphFielname', payload.file);
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
          systemLogs: [],
          ws: null,
          webSocketIsConnected: false,
          indiIsConnected: false,
          lastUpdate: null,
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
        return { time, indi }
      }
  }