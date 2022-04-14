<template>
    <button :disabled="disabled" @click="onClick">{{ label }}</button>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
button {
    width: 2em;
    height: 2em;
    border-radius: 50%;
    overflow: hidden;
    padding: 0.5em;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import MaterialIcon from '../basic/MaterialIcon.vue';

export default {
    mixins: [indi, utils],
    props: ["device", "property", "indiId", "disabled", "label"],
    components: {
        MaterialIcon,
    },
    methods: {
        onClick() {
            this.sendIndiNew(this.thisDevice, this.thisProperty, this.thisElement, "On");
        }
    }
}
</script>