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
        }
    }
}
