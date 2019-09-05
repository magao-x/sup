<template>
    <div>
        <div v-for="elem in property.elements" :key="elem.name">
            <indi-element :device="device" :property="property" :element="elem" />
        </div>
    </div>
</template>
<style scoped>

</style>
<script>
import IndiElement from "./IndiElement.vue";

export default {
    components: {
        IndiElement
    },
    props: ["device", "property"],
}
</script>
