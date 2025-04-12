<template>
    <span class="material-icons" >{{ name }}</span>
</template>
<style scoped>
    .material-icons {
        font-size: 1.6em;
        line-height: 0.4em;
        vertical-align: bottom;
    }
</style>
<script>
export default {
    props: ["name"]
}
</script>