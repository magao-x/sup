<template>
  <div class="plant-status">
    <cytoscape class="view graph"></cytoscape>
    <div class="view logs">
      <log-stream></log-stream>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@use "./css/variables.scss" as *;

.plant-status {
  display: grid;
  grid-template-columns: 3fr 2fr;
  grid-gap: $unit;
  padding: $unit;
  height: 100%;
  box-sizing: border-box;
}
.graph {
  box-sizing: border-box;
  
}
</style>
<script>
import Cytoscape from "~/components/basic/Cytoscape.vue";
import LogStream from "~/components/instrument/LogStream.vue";



export default {
  components: {
    Cytoscape,
    LogStream
  }
}
</script>