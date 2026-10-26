<template>
  <div class="audible-alerts" v-if="available">
    <button
      class="btn square"
      :class="{ 'needs-permission': blocked }"
      :title="buttonTitle"
      @click="testOrAllow"
    >
      <material-icon :name="iconName"></material-icon>
    </button>
    <toggle-switch
      :value="enabled"
      label-off="silent"
      label-on="audible"
      @input="setEnabled"
    ></toggle-switch>
    <input
      v-if="showVolume"
      class="volume"
      type="range"
      min="0"
      max="1"
      step="0.05"
      :value="volume"
      :disabled="!enabled"
      title="Alert volume in this browser"
      @input="setVolume($event.target.value)"
    />
  </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;
.audible-alerts {
  display: inline-flex;
  align-items: center;
  gap: $smgap;
}
.needs-permission {
  border: 1px solid $danger-red;
}
.volume {
  width: 6 * $unit;
  align-self: center;
}
</style>
<script>
import utils from "@/mixins/utils.js";
import audibleAlerts from "@/audibleAlerts.js";
import MaterialIcon from "@/components/basic/MaterialIcon.vue";
import ToggleSwitch from "@/components/basic/ToggleSwitch.vue";

export default {
  mixins: [utils],
  inject: ["indi"],
  components: { MaterialIcon, ToggleSwitch },
  props: {
    // The volume slider is useful on the Maggie-o X panel, where there is room
    // for it, and clutter in the status bar.
    showVolume: { type: Boolean, default: false },
  },
  computed: {
    device() {
      const config = this.$store.state.config;
      return config ? config.audible_alerts_device : null;
    },
    available() {
      // Nothing to listen to unless the device is actually running.
      return !!this.device && this.indiIdExists(`${this.device}.playback`);
    },
    enabled() {
      return this.$store.state.audibleAlerts.enabled;
    },
    blocked() {
      return this.$store.state.audibleAlerts.blocked;
    },
    volume() {
      return this.$store.state.audibleAlerts.volume;
    },
    iconName() {
      if (this.blocked) {
        return "volume_off";
      }
      return this.enabled ? "volume_up" : "volume_mute";
    },
    buttonTitle() {
      if (this.blocked) {
        return "This browser blocked audio playback; click to allow it";
      }
      return "Play a test tone in this browser";
    },
  },
  methods: {
    setEnabled(enabled) {
      // Both paths run straight out of the click, which is what lets the
      // browser treat the resulting playback as user-initiated.
      if (enabled) {
        audibleAlerts.enable();
      } else {
        audibleAlerts.disable();
      }
    },
    testOrAllow() {
      audibleAlerts.playChime();
    },
    setVolume(volume) {
      audibleAlerts.setVolume(volume);
    },
  },
};
</script>
