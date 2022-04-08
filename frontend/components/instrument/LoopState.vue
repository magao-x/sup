<template>
    <div class="loop status-indicator ">
      <span class="loop-state" :class="state">{{ state }}</span>
    </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.loop {
  color: white;
  background: var(--bg-alternate);
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
    state: function() {
      if (!this.thisDevice) return "waiting for AO state";
      return "loop " + this.thisDevice.properties['loopState'].elements['state'].value;
    },
    gain: function() {
      if (!this.thisDevice) return "?";
      return this.thisDevice.properties['loopGain'].elements['gain'].value;
    }
  }
};
</script>
