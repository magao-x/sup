<template>
    <div class="property">
        <p>{{ device.name }}.{{ property.name }} ({{ property.kind }}, <indi-light :state="property.state"></indi-light>)</p>
        <p v-if="property.message">{{ property.message }}</p>
        <template v-if="property.kind == 'swt'">
            <indi-switch-multi-element :device="device" :property="property" />
        </template><template v-else>
            <indi-element v-for="elem in objectAsSortedArray(property.elements)" :key="elem.name" :device="device" :property="property" :element="elem" />
        </template>
    </div>
</template>
<style scoped>
.property {
    border: 1px solid lightgreen;
    padding: 1rem;
}
</style>
<script>
import IndiElement from "./IndiElement.vue";
import IndiLight from "./IndiLight.vue";
import IndiSwitchMultiElement from "./IndiSwitchMultiElement.vue";
import utils from "./utils.js";

export default {
    components: {
        IndiElement,
        IndiSwitchMultiElement,
        IndiLight
    },
    props: ["device", "property"],
    mixins: [utils]
}
</script>
