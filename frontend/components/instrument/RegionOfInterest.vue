<template>
  <div class="roi-control">
    <sync-button @sync="onSync"></sync-button>
    <div class="roi">
      <div class="box"></div>
      <div class="position">
        (x=
        <input :value="x" />, y=
        <input :value="y" />)
      </div>
      <div class="height">
        h=
        <input :value="h" />
      </div>
      <div class="bin">
        bin
        <br />
        <input class="small" :value="bin_x" />&times;
        <input class="small" :value="bin_y" />
      </div>
      <div class="width">
        w=
        <input :value="w" />
      </div>
    </div>
    <commit-button @commit="onCommit"></commit-button>
  </div>
</template>
<style lang="scss" scoped>
body {
  height: 100vh;
  padding: 0;
  margin: 0;
}
.roi {
  font-size: 0.75rem;
  position: relative;
  box-sizing: border-box;
  width: 12em;
  height: 12em;
  overflow: hidden;
  border: 1px solid;
  input {
    min-width: 0;
    font: inherit;
    line-height: inherit;
    border: none;
    border-bottom: 1px solid;
    width: 2.5em;
    padding: 0.125em;
    margin: 0;
    &.small {
      width: 1rem;
    }
  }
  .position {
    position: absolute;
    top: 0.2em;
    left: 0.2em;
  }
  .box {
    width: 7em;
    height: 7em;
    border: 1px solid;
    position: absolute;
    top: 2.5em;
    left: 3.25em;
  }
  .width {
    left: 4em;
    bottom: 0.2em;
    position: absolute;
  }
  .height {
    top: 5.5em;
    left: 0.2em;
    position: absolute;
  }
  .bin {
    left: 5em;
    top: 4em;
    position: absolute;
    text-align: center;
    input {
      text-align: inherit;
    }
  }
}
</style>
<script>
import SyncButton from "~/components/basic/SyncButton.vue";
import CommitButton from "~/components/basic/CommitButton.vue";

export default {
    props: ["x", "y", "w", "h", "bin_x", "bin_y"],
    components: {
      SyncButton,
      CommitButton
    }
};
</script>