<template>
  <div class="observer-control">
    <div class="cols">
      <div class="col">
        <div class="recording">
          <indi-toggle-switch
            class="full-width"
            indi-id="observers.obs_on.toggle"
            label-on="Recording"
            label-off="Off"
          ></indi-toggle-switch>
        </div>
        <div class="purpose">
          <!-- <span class="label">Purpose:</span> -->
          <indi-current-target indi-id="observers.obs_name" style="flex: 1" prefix="Purpose:"></indi-current-target>
        </div>
      </div>
      <div class="col current-observer">
        <div>
          <span class="label">Current observer:</span>
          <indi-value indi-id="observers.current_observer.pfoa"></indi-value>
        </div>
        <div>
          Full name:
          <indi-value
            indi-id="observers.current_observer.full_name"
          ></indi-value>
        </div>
        <div>
          Institution:
          <indi-value
            indi-id="observers.current_observer.institution"
          ></indi-value>
        </div>
        <div>
          Email:<indi-switch-dropdown
            indi-id="observers.observers"
          ></indi-switch-dropdown>
        </div>
      </div>
    </div>
    <div class="writing-toggles">
      <div v-for="camName in camNames" :key="camName">
        <div>write {{ camName }}</div>
        <indi-toggle-switch
          v-if="!isObserving"
          :indi-id="`observers.writers.cam${camName}`"
          label-off=""
          label-on=""
        ></indi-toggle-switch>
        <div v-else-if="retrieveValueByIndiId(`cam${camName}-sw.writing.toggle`) == 'On'" class="glowy">
          <material-icon name="power_settings_new"></material-icon>
        </div>
        <div v-else class="notGlowy">
          <material-icon name="highlight_off"></material-icon>
        </div>
        <div><indi-value 
          :indi-id="`cam${camName}-sw.writing.toggle`"
          :placeholder="`looking for cam${camName}-sw...`"
          on-text="writing"
          off-text="ready"
        ></indi-value></div>
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.label {
  font-weight: bold;
}


.full-width {
  width: 100%;
}

.recording {
  font-size: 125%;
  text-align: center;
  padding: $medgap 0;
}
.purpose {
  font-size: 125%;
  display: flex;
}

.writing-toggles {
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
  display: grid;
  gap: $unit;
  text-align: center;
  width: 100%;
}

.current-observer {
  line-height: 1.7em;
}
.save-path {
  font-family: monospace;
}

.glowy {
  text-shadow: 0 0 5 $plasma-blue; /* Initial shadow */
  animation: pulse 1s infinite alternate; /* Animation */
  color: $plasma-blue;
}
.notGlowy {
  color: $icon-gray;
}

@keyframes pulse {
  0% {
    text-shadow: 0 0 5px $plasma-blue; /* Initial shadow */
  }
  100% {
    text-shadow: 0 0 20px $plasma-blue; /* Pulsing shadow */
  }
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiSwitchDropdown from "../indi/IndiSwitchDropdown.vue";
import IndiToggleSwitch from "../indi/IndiToggleSwitch.vue";
import AlternateIndiToggleSwitch from "../indi/AlternateIndiToggleSwitch.vue";
import IndiElement from "../indi/IndiElement.vue";
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiCurrentTarget from "~/components/indi/IndiCurrentTarget.vue";
import MaterialIcon from "~/components/basic/MaterialIcon.vue";

export default {
  props: {
    device: {
      type: String,
      default: "observers",
    },
    camNames: {
      type: Array,
      default: () => ["sci1", "sci2", "wfs", "lowfs", "tip", "acq"],
    },
  },
  computed: {
    isObserving() {
      return this.retrieveValueByIndiId("observers.obs_on.toggle") == "On";
    }
  },
  mixins: [indi, utils],
  components: {
    IndiValue,
    IndiSwitchMultiElement,
    IndiSwitchDropdown,
    IndiToggleSwitch,
    IndiElement,
    IndiProperty,
    IndiCurrentTarget,
    AlternateIndiToggleSwitch,
    MaterialIcon
  },
};
</script>