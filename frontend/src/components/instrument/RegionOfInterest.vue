<template>
  <div class="roi-control">
    <div>Region of Interest:</div>
    <div class="roi">
      <div class="box"></div>
      <div class="position">
        (x=
        <input :value="vals.x" :disabled="isDisabled" />
        , y=
        <input :value="vals.y" :disabled="isDisabled" />
        )
      </div>
      <div class="height">
        h=
        <input :value="vals.h" :disabled="isDisabled" />
      </div>
      <div class="bin">
        bin
        <br />
        <input class="small" :value="vals.bin_x" :disabled="isDisabled" />&times;
        <input class="small" :value="vals.bin_y" :disabled="isDisabled" />
      </div>
      <div class="width">
        w=
        <input :value="vals.w" />
      </div>
    </div>
    <sync-button @sync="onSync" :disabled="isDisabled"></sync-button>
    <commit-button @commit="onCommit" labeled="true" :disabled="isDisabled"></commit-button>
  </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;
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
    background: var(--inset-bg);
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
import SyncButton from "@/components/basic/SyncButton.vue";
import CommitButton from "@/components/basic/CommitButton.vue";
import indi from "@/mixins/indi.js";

const keys = ["x", "y", "w", "h", "bin_x", "bin_y"];

export default {
  mixins: [indi],
  props: {
    device: {
      type: Object
    },
    indiId: {
      type: String
    }
  },
  methods: {
    onSync: function () {
      
    },
    onCommit: function () {
      
    }
  },
  data() {
    let userInput = {};
    let shouldUpdate = {};
    let isModified = {};
    for (const k in keys) {
      userInput[k] = null;
      shouldUpdate[k] = true;
      isModified[k] = false;
    }
    return {
      userInput,
      shouldUpdate,
      isModified
    };
  },
  components: {
    SyncButton,
    CommitButton
  },
  computed: {
    vals() {
      let out = {};
      for (const k of keys) {
        if (this.shouldUpdate[k] === false && this.userInput[k] !== null) {
          out[k] = this.userInput[k];
        } else {
          out[k] = this.currentValue[k];
        }
      }
      return out;
    },
    currentValue() {
      let out = {};
      for (const k of keys) {
        if (this.indiDefined) {
          console.log(k);
          out[k] = this.thisDevice[k]._elements["current"]._value;
        } else {
          out[k] = null;
        }
      }
      return out;
    },
    isDisabled: function() {
      return true;
    }
  }
};
</script>
