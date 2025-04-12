<template>
  <div>
  <button :disabled="!couldScram || preparing" class="scram red" @click="prepareToScram">SCRAM</button>
  <button v-if="preparing" class="scram red" @click="scram">really 🙀 SCRAM 🙀</button>
  <button v-if="preparing" @click="cancel">cancel</button>
  </div>
</template>

<script>
import utils from "~/mixins/utils.js";

const cameras = ["camsci1", "camsci2", "camwfs"];
const loops = ["camwfs-align", "holoop", "loloop"];
const tcsiOffloads = ["offlF", "offlTT"];

export default {
  mixins: [utils],
  data() {
    return {
      preparing: false
    }
  },
  computed: {
    couldScram() {
      let flag = false;
      for (let name of cameras) {
        const shutterState = this.retrieveValueByIndiId(`${name}.shutter.toggle`);
        const shutterPower = this.retrieveValueByIndiId(`${name}.shutter_status.status`) !== "POWEROFF";
        flag = flag || (shutterPower && (shutterState == "Off"));
      }
      for (let loopName of loops) {
        const loopState = this.retrieveValueByIndiId(`${loopName}.loop_state.toggle`) == "On";
        flag = flag || loopState;
      }
      for (let offloadName of tcsiOffloads) {
        flag = flag || (this.retrieveValueByIndiId(`tcsi.${offloadName}.toggle`) == "On");
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
      for (let name of cameras) {
        this.indi.sendIndiNewByNames(name, "shutter", "toggle", "On");
        this.indi.sendIndiNewByNames(name, "emgain", "target", 1);
      }
      for (let loopName of loops) {
        this.indi.sendIndiNewByNames(loopName, "loop_state", "toggle", "Off");
      }
      for (let offloadName of tcsiOffloads) {
        this.indi.sendIndiNewByNames("tcsi", offloadName, "toggle", "Off");
      }
      this.preparing = false;
    }
  }
}
</script>

<style lang="scss" scoped>
@use "~/css/variables.scss";
button {
  display: block;
  width: 100%;
}
</style>