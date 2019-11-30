import { sprintf } from '~/node_modules/printj/printj.mjs';

export default {
  methods: {
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
    },
    applyFormatString: function (format, number) {
      if (number === null) {
        return "";
      } else {
        return sprintf(format, number);
      }
    },
    precisionFromFormat: function (format) {
      // based on the old POSIX style regex from
      // https://github.com/SheetJS/printj/blob/master/README.md
      // /%(?:
      //     ([-])?                             # flags (only minus sign)
      //     (\d+|\*)?                          # width
      //     (?:\.(\d+|\*))?                    # period + precision
      //     ([hl])?                            # length
      //     ([dioxXucsfeEgGp%])                # conversion specifier
      // )/x
      //
      // groups:
      // 0: whole match
      // 1: flags
      // 2: width
      // 3: precision
      // 4: length
      // 5: type
      const regex = /%(?:([-])?(\d+|\*)?(?:\.(\d+|\*))?([hl])?([dioxXucsfeEgGp%]))/;
      const matches = regex.exec(format);
      const precision = Number(matches[3]);
      const type = matches[5];
      return [precision, type];
    },
    stepFromFormat: function (format, trueStep) {
      const [precision, type] = this.precisionFromFormat(format);
      let stepSize = trueStep;
      if ('diu'.search(type) !== -1) {
        stepSize = 1;
      } else {
        if (!isNaN(precision)) {
          stepSize = Math.pow(10, -Number(precision));
        }
      }
      return stepSize;
    },
    objectAsSortedArray: function (ob) {
      let keys = Object.keys(ob).sort();
      return keys.map((val) => ob[val]);
    }
  }
}
