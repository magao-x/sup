<template>
    <button :disabled="disabled" @click="onClick">{{ label }}</button>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

</style>
<script>
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";
import MaterialIcon from '@/components/basic/MaterialIcon.vue';

export default {
    mixins: [indi, utils],
    props: ["device", "property", "indiId", "disabled", "label"],
    components: {
        MaterialIcon,
    },
    methods: {
        onClick(ev) {
            if (!this.disabled) {
                this.sendIndiNew(this.thisProperty, this.thisElement, "On");
            }
            return false;
        }
    }
}
</script>