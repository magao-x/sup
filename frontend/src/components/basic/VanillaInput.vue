<template>
    <input :value="value" @input="$emit('input', $event.target.value)">
</template>
<script>
export default {
    props: ["value"]
}
</script>