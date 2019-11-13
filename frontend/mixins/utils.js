import { sprintf } from '~/node_modules/printj/printj.mjs';

export default {
  methods: {
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
