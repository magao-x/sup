<template>
<div>
    <div :id="elementID"></div>
</div>
</template>
<style scoped>
</style>
<script>

export default {
    data() {
        return {
            celestialMap: null
        }
    },
    computed: {
        elementID() {
            return this.$id('celestial');
        }
    },
    mounted() {
        console.log(Celestial);
    }
}
</script>