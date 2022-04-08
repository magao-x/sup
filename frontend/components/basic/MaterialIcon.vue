<template>
    <span class="material-icons" >{{ name }}</span>
</template>
<style scoped>
    .material-icons {
        font-size: 150%;
        line-height: 0.5;
    }
</style>
<script>
export default {
    props: ["name"]
}
</script>