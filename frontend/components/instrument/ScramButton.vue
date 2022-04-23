<template>
  <div>
  <button :disabled="!couldScram || preparing" class="scram red" @click="prepareToScram">SCRAM</button>
  <button v-if="preparing" class="scram red" @click="scram">really 🙀 SCRAM 🙀</button>
  <button v-if="preparing" @click="cancel">cancel</button>
  </div>
</template>

<script>
import utils from "~/mixins/utils.js";
export default {
  mixins: [utils],
  data() {
    return {
      preparing: false
    }
  },
  props: {
    camNames: {
      type: Array,
      default: () => ["camsci1", "camsci2", "camlowfs"]
    }
  },
  computed: {
    couldScram() {
      let flag = false;
      for (let name of this.camNames) {
        flag = flag || (this.retrieveValueByIndiId(`${name}.shutter.toggle`) == "Off");
      }
      return flag;
    }
  },
  methods: {
    prepareToScram() {
      this.preparing = true;
    },
    cancel() {
      this.preparing = false;
    },
    scram() {
      for (let name of this.camNames) {
        this.sendIndiNewByNames(name, "shutter", "toggle", "On");
      }
      this.preparing = false;
    }
  }
}
</script>

<style lang="scss" scoped>
@import "~/css/variables.scss";
button {
  display: block;
  width: 100%;
}
</style>