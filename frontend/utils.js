import { sprintf } from '~/../node_modules/printj/printj.mjs';

export default {
    methods: {
        objectAsSortedArray: function (ob) {
            let keys = Object.keys(ob).sort();
            return keys.map((val) => ob[val]);
        },
        receivedProperty: function (devices, deviceName, propertyName) {
            if (devices[deviceName] !== undefined && devices[deviceName].properties[propertyName] !== undefined) {
                return true;
            } else {
                console.log('no prop', deviceName, propertyName);
            }
        },
        applyFormatString: function(format, number) {
            let formatted = sprintf(format, number);
            console.log(formatted);
            return formatted;
        },
        stepFromFormat: function(format, trueStep) {
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
            console.log(matches);
            const precision = Number(matches[3]);
            const type = matches[5];
            let stepSize = trueStep;
            if ('diu'.search(type) !== -1) {
                stepSize = 1;
            } else {
                if (!isNaN(precision)) {
                    stepSize = Math.pow(10, -Number(precision));
                }
            }
            return stepSize;
        }
    }
}
