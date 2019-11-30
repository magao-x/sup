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
    },
    thisIndiId: function () {
      if (this.thisElement) {
        return `${this.thisDevice.name}.${this.thisProperty.name}.${this.thisElement.name}`;
      } else if (this.thisProperty) {
        return `${this.thisDevice.name}.${this.thisProperty.name}`;
      } else if (this.thisDevice) {
        return this.thisDevice.name;
      } else {
        return null;
      }
    },
    indiDefined() {
      if (this.thisIndiId !== null) return true;
      else return false;
    }
  },
  methods: {
    sendIndiNew: function (device, property, element, value) {
      const payload = {
        'device': device.name,
        'property': property.name,
        'element': element.name,
        'value': value
      };
      this.$socket.emit('indi_new', payload);
      console.log('Emitted indi_new', payload)
    }
  }
}
