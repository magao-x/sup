<template>
  <div class="observer-control view">
    <div class="cols">
      <div class="col">
        <div class="recording">
          <indi-toggle-switch
            class="full-width"
            indi-id="observers.obs_on.toggle"
            label-on="Recording"
            label-off="Off"
            :prompt="true"
          ></indi-toggle-switch>
        </div>
        <div>
          <span class="label">Purpose:</span>
          <indi-value indi-id="observers.obs_name.current"></indi-value>
        </div>
        <div>
          <indi-element indi-id="observers.obs_name.target"></indi-element>
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
      <indi-switch-multi-element  indi-id="observers.writers"></indi-switch-multi-element>
      <!-- <div v-for="camName in camNames" :key="camName">
        <div>write {{ camName }}</div>
        <indi-toggle-switch
          :indi-id="`cam${camName}-sw.writing.toggle`"
          label-off=""
          label-on=""
          :prompt="true"
        ></indi-toggle-switch>
      </div> -->
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
</style>
<script>
import indi from "~/mixins/indi.js";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiSwitchDropdown from "../indi/IndiSwitchDropdown.vue";
import IndiToggleSwitch from "../indi/IndiToggleSwitch.vue";
import IndiElement from "../indi/IndiElement.vue";
import IndiProperty from "~/components/indi/IndiProperty.vue";

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
  mixins: [indi],
  components: {
    IndiValue,
    IndiSwitchMultiElement,
    IndiSwitchDropdown,
    IndiToggleSwitch,
    IndiElement,
    IndiProperty,
  },
  computed: {},
};
</script>