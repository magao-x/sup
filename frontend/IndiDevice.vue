<template>
  <div>
    <p>{{ device.name }}</p>
    <div v-for="prop in device.properties" :key="device.name + '.' + prop.name">
      <p>{{ device.name }}.{{ prop.name }} ({{ prop.kind }}, {{ prop.state }})</p>
      <p v-if="prop.message">{{ prop.message }}</p>
      <indi-property :device="device" :property="prop" />
    </div>
  </div>
</template>
<style scoped>

</style>
<script>
import IndiProperty from "./IndiProperty.vue";

export default {
  props: ["device"],
  components: {
    IndiProperty
  }
}
</script>
