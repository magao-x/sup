import { sprintf } from 'printj';
import constants from "@/constants.js";
import { DateTime, Duration } from "luxon";
export default {
  inject: ['time', "indi"],
  methods: {
    retrieveByIndiId: function (indiId) {
      const parts = indiId.split('.');
      const deviceName = parts.shift();
      if (typeof this.indi.world[deviceName] !== "undefined") {
        const device = this.indi.world[deviceName];
        if (parts.length > 0) {
          const propName = parts.shift();
          if (typeof device[propName] !== "undefined") {
            const property = device[propName];
            if (parts.length > 0) {
              const eltName = parts.shift();
              if (typeof property._elements[eltName] !== "undefined") {
                const element = property._elements[eltName];
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
      if (elt && elt.hasOwnProperty('_value')) {
        return elt._value;
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
    },
    sendIndiNew: function (property, element, value) {
      this.indi.sendIndiNewByNames(property.device, property.name, element.name, value);
    },
    scheduleSemester(ts) {
      let semester = ts.month > 6 ? 'B' : 'A';
      return ts.toFormat("yyyy") + semester;
    },
    formatSeconds(secs) {
      console.log(secs);
      let out = [];
      const hours = Math.floor(secs / (60 * 60));
      let minutes = Math.floor((secs - 60 * 60 * hours) / 60);
      let seconds = Math.round(secs - 60 * 60 * hours - 60 * minutes);
      if (seconds == 60) {
        // edge case where rounding up gets a whole minute
        minutes += 1;
        seconds = 0;
      }
      if (hours > 0) {
        out.push(`${hours}h`);
      }
      if (hours > 0 || minutes > 0) {
        out.push(`${minutes}m`);
      }
      out.push(`${seconds}s`);
      out.reverse();
      let outStr = out.pop();
      console.log(out, hours, minutes, seconds);
      for (let part of out) {
        outStr += " " + part;
        console.log(outStr);
      }
      return outStr;
    },
    dateNightFromDateTime(ts) {
      // (JS port of the datestamp_strings_from_ts function in lookyloo that does this)
      // if the span begins before noon Chile time on the given D, the
      // stringful timestamp is "YYYY-MM-(D-1)_D" because we observe over
      // UTC night of one day into morning of the next.

      // note that daylight saving doesn't change the day, so we just use
      // UTC-4 for CLST
      // modified = roughly local Chile time for the start of the span
      const oneDay = Duration.fromObject({days: 1});
      const modified = ts.minus(Duration.fromObject({hours: 4}));
      let startDate;
      if (modified.hour < 12) {
        // if span started before noon, assume it was the previous night UTC
        startDate = modified.minus(oneDay)
      } else {
        // otherwise chile date == utc date
        startDate = modified;
      }

      let endDate = startDate.plus(oneDay);
      let dayString = startDate.toISODate();
      let endPart = "";
      if (endDate.year !== startDate.year) {
        endPart += endDate.toFormat("yyyy") + "-";
      }
      if (endDate.month !== startDate.month) {
        endPart += endDate.toFormat("MM") + "-";
      }
      endPart += endDate.toFormat("dd");
      dayString += "_" + endPart;
      return dayString;
    },

  }
}
