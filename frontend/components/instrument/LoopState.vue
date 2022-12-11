<template>
    <div class="loop status-indicator">
      <span class="loop-state" :class="state">{{ state }} {{ gain }}</span>
    </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.loop {
  color: white;
}

.waiting {
  color: var(--fg-neutral);
}

.open {
  color: var(--fg-negative);
  color: $warning;
}

.closed {
  color: var(--fg-positive);
  color: $plasma-blue;
}

.paused {
  color: $alert;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  mixins: [indi, utils],
  props: ["device", "indiId"],
  computed: {
    loopClosed: function () {
      return this.thisDevice['loop_state']._elements['toggle']._value == "On";
    },
    state: function() {
      if (!(this.thisDevice && this.thisDevice.loop_state)) return "waiting for AO state";
      const clopen = this.loopClosed ? "closed" : "open";
      return `${this.indiId} ${clopen}`;
    },
    gain: function() {
      if (!this.thisDevice) return "?";
      if (!this.loopClosed) return "";
      const gain = this.thisDevice['loop_gain']._elements['current']._value
      return gain.toFixed(2);
    }
  }
};
</script>
