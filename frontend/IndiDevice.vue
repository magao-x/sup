<template>
  <div>
    <p>{{ name }}</p>
    <div v-for="(prop, propName) in device">
      {{ prop._kind }}
      <div v-if="prop._kind == 'SWITCH'">switch component here</div>
      <div v-if="prop._kind == 'NUMBER'">number component here</div>
      <div v-if="prop._kind == 'LIGHT'">light component here</div>
      <div v-if="prop._kind == 'TEXT'">text component here</div>
      <div v-for="(elem, elemName) in prop.elements">
        <div>
          {{ prop.state }} {{ prop.group }} {{ prop.label }} {{ name }}.{{ propName }}.{{ elemName }}={{ elem.value }} {{ prop.perm }}
          <input v-if="prop.perm == 'rw'" :placeholder="elem.value">
        </div>
      </div>
    </div>
    <button @click="$emit('deviceChange')">emit deviceChange</button>
  </div>
</template>
<style scoped>

</style>
<script>
export default {
  props: ["name", "device"]
}
</script>
