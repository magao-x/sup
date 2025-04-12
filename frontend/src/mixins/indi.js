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
    thisDeviceName: function() {
      return this.thisIndiId?.split('.')[0];
    },
    thisIndiId: function () {
      if (this.thisElement) {
        return `${this.thisProperty.device}.${this.thisProperty.name}.${this.thisElement.name}`;
      } else if (this.thisProperty) {
        return `${this.thisProperty.device}.${this.thisProperty.name}`;
      } else if (this.thisDevice) {
        for(let k of Object.keys(this.thisDevice)) {
          return this.thisDevice[k].device;
        }
        
      } else {
        return null;
      }
    },
    indiDefined() {
      if (this.thisIndiId !== null) return true;
      else return false;
    }
  }
}
