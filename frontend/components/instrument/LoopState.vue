<template>
  <div>
    <div class="loop-state" :class="state">
      loop: {{ state }}
    </div>
    <div>
      gain: {{ gain }}
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.waiting {
  color: inherit;
}

.open {
  color: $warning;
}

.closed {
  color: $primary;
}

.paused {
  color: $magenta;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  mixins: [indi, utils],
  props: ["device", "indiId"],
  computed: {
    state: function() {
      if (!this.thisDevice) return "waiting";
      return this.thisDevice.properties['loopState'].elements['state'].value;
    },
    gain: function() {
      if (!this.thisDevice) return "?";
      return this.thisDevice.properties['loopGain'].elements['gain'].value;
    }
  }
};
</script>