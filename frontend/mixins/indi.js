export default {
  computed: {
    thisDevice: function () {
      if (this.device) return this.device;
      if (!this.indiId) return null;
      return this.retrieveDeviceByIndiId(this.indiId);
    },
    thisProperty: function () {
      if (this.property) return this.property;
      if (!this.indiId) return null;
      const numParts = this.indiId.split(".").length;
      if (numParts < 2) return null;
      return this.retrievePropertyByIndiId(this.indiId);
    },
    thisElement: function () {
      if (this.element) return this.element;
      if (!this.indiId) return null;
      const numParts = this.indiId.split(".").length;
      if (numParts < 3) return null;
      return this.retrieveByIndiId(this.indiId);
    }
  },
  methods: {
    sendIndiNew: function (device, property, element, value) {
      console.log("In sendIndiNew");
      const payload = {
        'device': device.name,
        'property': property.name,
        'element': element.name,
        'value': value
      };
      this.$socket.emit('indi_new', payload);
      console.log(payload);
    },
    retrieveByIndiId: function (indiId) {
      const parts = indiId.split('.');
      const deviceName = parts.shift();
      if (typeof this.$store.state.devices[deviceName] !== "undefined") {
        const device = this.$store.state.devices[deviceName];
        if (parts.length > 0) {
          const propName = parts.shift();
          if (typeof device.properties[propName] !== "undefined") {
            const property = device.properties[propName];
            if (parts.length > 0) {
              const eltName = parts.shift();
              if (typeof property.elements[eltName] !== "undefined") {
                const element = property.elements[eltName];
                return element;
              } else {
                return null;
              }
            } else {
              return property;
            }
          } else {
            return null;
          }
        } else {
          return device;
        }
      } else {
        return null;
      }
    },
    retrieveValueByIndiId: function (indiId) {
      const elt = this.retrieveByIndiId(indiId);
      if (elt && elt.hasOwnProperty('value')) {
        return elt.value;
      } else {
        return null;
      }
    },
    retrieveDeviceByIndiId: function (indiId) {
      const [devName, ...rest] = indiId.split(".");
      return this.retrieveByIndiId(devName);
    },
    retrievePropertyByIndiId: function (indiId) {
      const [devName, propName, ...rest] = indiId.split(".");
      return this.retrieveByIndiId(devName + '.' + propName);
    },
    retrieveElementByIndiId: function (indiId) {
      return this.retrieveByIndiId(indiId);
    },
    indiIdExists: function (indiId) {
      return this.retrieveByIndiId(indiId) !== null;
    }
  }
}
