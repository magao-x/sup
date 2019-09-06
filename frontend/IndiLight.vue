<template>
  <div class="light" :class="{'idle': state == 'Idle', 'ok': state == 'Ok', 'busy': state == 'Busy', 'alert': state == 'Alert'}">
    {{ state }}
  </div>
</template>
<style lang="scss" scoped>
.light {
  border: 1px solid black;
  padding: 0.5rem;
  border-radius: 0.25rem;
  display: inline-block;
}
.alert {
    color: orange;
}
.ok {
    color: lightgreen;
}
.busy {
    color: gray;
}
.idle {
    color: white;
}
</style>
<script>

export default {
  props: ["state"]
}
</script>
