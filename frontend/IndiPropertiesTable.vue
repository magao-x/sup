<template>
    <div class="indi-properties-table">
        <div class="search-control"><span class="search-icon"><i class="material-icons">search</i></span><input v-model="searchString"></div>
        <table>
        <thead>
            <tr>
            <th>state</th>
            <th>device</th>
            <th>property</th>
            <th class="kind">kind</th>
            <th>element</th>
            <th>value</th>
            <th class="controls">control</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="record in flattenedDevices" :key="record.device.name + '.' + record.property.name + '.' + record.element.name" :class="record.property.state">
            <td><indi-light :state="record.property.state"></td>
            <td>{{ record.device.name }}</td>
            <td>{{ record.property.name }}</td>
            <td class="kind">{{ record.property.kind }}</td>
            <td>{{ record.element.name }}</td>
            <td>{{ record.element.value }}</td>
            <td class="controls"><indi-element :device="record.device" :property="record.property" :element="record.element"></indi-element></td>
            </tr>
        </tbody>
        </table>
    </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';
.indi-properties-table {
        width: 100%;
}
.search-control {
    position: relative;
    display: flex;
    .search-icon {
        position: absolute;
        left: 0.5 * $unit;
        width: $unit;
        top: 0.25 * $unit;
        box-sizing: border-box;
    }
    input {
        padding-left: 2 * $unit;
        flex: 1;
    }
}


table {
    border-collapse: collapse;
    width: 100%;

    text-align: center;
    tbody > tr:nth-child(odd) {
        background: $base02;
    }
    tbody > tr:hover {
        background: lighten($base02, 5);
    }
    td, th {
        // width: 14.2%;
        box-sizing: border-box;
        padding: 0 $unit;
    }
    .kind {
        width: 8%;
    }
    .controls {
        text-align: left;
        // padding-left: $unit;
        max-width: 20em;
    }
}
</style>
<script>
import IndiElement from "./IndiElement.vue";
import IndiLight from "./IndiLight.vue";
import utils from "./utils.js";

export default {
    components: {
        IndiElement,
        IndiLight
    },
    props: ["devices"],
    mixins: [utils],
    computed: {
        flattenedDevices() {
            const devs = [];
            for (let device of this.objectAsSortedArray(this.devices)) {
                for (let property of this.objectAsSortedArray(device.properties)) {
                for (let element of this.objectAsSortedArray(property.elements)) {
                    devs.push({
                    device,
                    property,
                    element
                    })
                }
                }
            }
            return devs;
            }
    },
    data: function () {
        return {searchString: ""}
    }
}
</script>
