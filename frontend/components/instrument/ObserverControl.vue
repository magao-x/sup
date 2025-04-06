<template>
  <div class="observer-control" :class="{ 'active': isObserving }" v-if="indiDefined">
    <div class="metadata">
      <span>Current observer:</span>
      <indi-switch-dropdown indi-id="observers.observers"></indi-switch-dropdown>
      <span class="spaced">Target Name:</span>
      <indi-current-target indi-id="observers.target" width="20em"></indi-current-target>
      <span class="spaced">Observation Name:</span>
      <indi-current-target indi-id="observers.obs_name" width="20em"></indi-current-target>
    </div>
    <div style="display: flex;">
      <div class="recording"><indi-toggle-switch id="recording" indi-id="observers.obs_on.toggle" label-on="Recording"
          label-off="Off"></indi-toggle-switch>
      </div>
      <div class="section totals">
        <span class="group-label">
          total
        </span>
        <div class="totals-grid">
          <div :class="{ glowy: isObserving }">{{ observationTimeTotal }}</div>
          <div :class="{ glowy: isObserving }">{{ observationDeltaParang }}º</div>
          <div>{{ targetTimeTotal }}</div>
          <div>{{ targetDeltaParang }}º</div>
        </div>
      </div>
      <div class="all-toggles">
        <div v-for="(names, group) in streamNames" class="toggles section">
          <span class="group-label">{{ group }}</span>
          <div v-for="name in names" class="stream" :class="{
            glowy: isObserving && retrieveValueByIndiId(`${name}-sw.writing.toggle`) == 'On',
            notGlowy: isObserving && retrieveValueByIndiId(`${name}-sw.writing.toggle`) == 'Off'
          }">
            <div class="label-text">{{ name }}</div>
            <alternate-indi-toggle-switch v-if="!isObserving" :stacked="true"
              :indi-id="`observers.writers.${name}`"></alternate-indi-toggle-switch>
            <div v-else-if="retrieveValueByIndiId(`${name}-sw.writing.toggle`) == 'On'">
              <material-icon name="power_settings_new"></material-icon>
            </div>
            <div v-else-if="retrieveValueByIndiId(`${name}-sw.writing.toggle`) == 'Off'">
              <material-icon name="more_horiz"></material-icon>
            </div>
            <div v-else>
              <material-icon name="link_off"></material-icon>
            </div>
          </div>
          <!-- <div v-else-if="retrieveValueByIndiId(`${name}-sw.writing.toggle`) == 'On'" class="glowy stream">
          <div class="label-text">{{ name }}</div>
          <material-icon name="power_settings_new"></material-icon>
        </div>
        <div v-else-if="retrieveValueByIndiId(`${name}-sw.writing.toggle`) == 'Off'" class="notGlowy stream">
          <div class="label-text">{{ name }}</div>
          <material-icon name="more_horiz"></material-icon>
        </div>
        <span v-else class="notGlowy stream">
          <div class="label-text">{{ name }}</div>
          <material-icon name="link_off"></material-icon>
        </span> -->
        </div>
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

#recording {
  margin-top: $unit;
}

.observer-control {
  background: var(--bg-alternate);
  .metadata {
    margin-bottom: $lggap;
  }
}

.section {
  border-left: 1px solid gray;
  position: relative;
  padding-left: 1rem;
  padding-right: 0.5rem;
  margin-left: $medgap;

  .group-label {
    position: absolute;
    left: 0;
    top: 0;
    writing-mode: vertical-lr;
    text-align: right;
    font-variant: small-caps;
    transform: rotate(180deg);
  }
}

.totals {
  min-width: 12em;

  .totals-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    text-align: right;
  }
}

.all-toggles {
  overflow-y: hidden;
  overflow-x: scroll;
  display: flex;
}

.toggles {
  display: flex;
  flex: 1;

  .label-text {
    line-height: 1.0;
    display: block;
    padding: 0.5rem;
  }


  .stream {
    text-align: center;

    .material-icons {
      display: block;
    }
  }
}

.glowy {
  text-shadow: 0 0 5px $plasma-blue;
  /* Initial shadow */
  animation: pulse 1s infinite alternate;
  /* Animation */
  color: $plasma-blue;
}

@keyframes pulse {
  0% {
    text-shadow: 0 0 5px $plasma-blue;
    /* Initial shadow */
  }

  100% {
    text-shadow: 0 0 20px $plasma-blue;
    /* Pulsing shadow */
  }
}

.label {
  font-weight: bold;
}

.full-width {
  width: 100%;
}

.recording {
  font-size: 125%;
  text-align: center;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiSwitchDropdown from "~/components/indi/IndiSwitchDropdown.vue";
import IndiToggleSwitch from "~/components/indi/IndiToggleSwitch.vue";
import AlternateIndiToggleSwitch from "~/components/indi/AlternateIndiToggleSwitch.vue";
import IndiElement from "~/components/indi/IndiElement.vue";
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiCurrentTarget from "~/components/indi/IndiCurrentTarget.vue";
import MaterialIcon from "~/components/basic/MaterialIcon.vue";

export default {
  props: {
    device: {
      type: String,
      default: "observers",
    },
    scienceCamNames: {
      type: Array,
      default: () => [
        "camsci1", "camsci2"
      ],
    },
  },
  computed: {
    isObserving() {
      return this.retrieveValueByIndiId(`${this.device}.obs_on.toggle`) == "On";
    },
    targetTimeTotal() {
      return this.formatSeconds(this.retrieveValueByIndiId(`${this.device}.obs_time.target`));
    },
    observationTimeTotal() {
      return this.formatSeconds(this.retrieveValueByIndiId(`${this.device}.obs_time.observation`));
    },
    targetDeltaParang() {
      return this.applyFormatString("%0.2f", this.retrieveValueByIndiId(`${this.device}.obs_delta_parang.target`));
    },
    observationDeltaParang() {
      return this.applyFormatString("%0.2f", this.retrieveValueByIndiId(`${this.device}.obs_delta_parang.observation`));
    },
    streamNames() {
      const writers = this.retrievePropertyByIndiId(`${this.device}.writers`);
      if (writers) {
        let names = Object.keys(writers._elements);
        const isSci = (val) => this.scienceCamNames.indexOf(val) > -1;
        const isDm = (val) => val.startsWith('dm');
        let sci = names.filter((val) => isSci(val));
        names = names.filter((val) => !isSci(val));
        let dm = names.filter((val) => isDm(val));
        let aux = names.filter((val) => !isDm(val));
        return {
          sci,
          aux,
          dm,
        }
      } else {
        return {};
      }
    },
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