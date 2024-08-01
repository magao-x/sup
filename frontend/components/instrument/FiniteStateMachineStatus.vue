<template>
  <span class="fsm" :class="fsmState.toLowerCase()" :title="fsmState.toLowerCase()"><span v-if="verbose">{{ fsmState }}</span> <material-icon :name="fsmStateIcon"></material-icon></span>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.failure, .error, .nodevice, .nothomed, .poweroff {
  color: $error;
}
.poweron, .notconnected, .connected, .loggedin, .configuring, .homing {
  color: $alert;
}
.ready, .operating {
  color: $icon-green;
}
.shutdown {
  color: $error;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import MaterialIcon from '~/components/basic/MaterialIcon.vue';

const stateToIcon = {
  waiting: "link_off",
  FAILURE: "dangerous",
  ERROR: "warning",
  UNINITIALIZED: "hourglass_top",
  INITIALIZED: "hourglass_bottom",
  NODEVICE: "sync_problem",
  POWEROFF: "power",
  POWERON: "power_settings_new",
  NOTCONNECTED: "link_off",
  CONNECTED: "link",
  LOGGEDIN: "link",
  CONFIGURING: "sync",
  NOTHOMED: "home",
  HOMING: "home",
  OPERATING: "all_inclusive",
  READY: "bolt",
  SHUTDOWN: "do_not_disturb_on",
};
// FAILURE=-20,       ///< The application has failed, should be used when m_shutdown is set for an error.
// ERROR=-10,         ///< The application has encountered an error, from which it is recovering (with or without intervention)
// UNINITIALIZED = 0, ///< The application is unitialized, the default
// INITIALIZED = 1,   ///< The application has been initialized, set just before calling appStartup().
// NODEVICE = 2,      ///< No device exists for the application to control.
// POWEROFF = 4,      ///< The device power is off.
// POWERON = 6,       ///< The device power is on.
// NOTCONNECTED = 8,  ///< The application is not connected to the device or service.
// CONNECTED = 10,     ///< The application has connected to the device or service.
// LOGGEDIN = 15,      ///< The application has logged into the device or service
// CONFIGURING = 20,   ///< The application is configuring the device.
// NOTHOMED = 24,     ///< The device has not been homed.
// HOMING = 25,       ///< The device is homing.
// OPERATING = 30,    ///< The device is operating, other than homing.
// READY = 35,        ///< The device is ready for operation, but is not operating.
// SHUTDOWN = 10000   ///< The application has shutdown, set just after calling appShutdown().

export default {
  components: { MaterialIcon },
  props: ["device", "indiId", "verbose"],
  mixins: [indi, utils],
  computed: {
    fsmState() {
      if (!this.indiDefined || !this.thisDevice.hasOwnProperty("fsm") || !this.thisDevice.fsm._elements.hasOwnProperty("state")) return "waiting";
      return this.thisDevice["fsm"]._elements["state"]._value;
    },
    fsmStateIcon() {
      return stateToIcon[this.fsmState];
    }
  }
}
</script>