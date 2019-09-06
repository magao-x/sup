export default {
    methods: {
        objectAsSortedArray: function (ob) {
            let keys = Object.keys(ob).sort();
            return keys.map((val) => ob[val]);
        }
    }
}
