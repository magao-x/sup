<template>
  <div class="observer-control" :class="{ 'active': isObserving }" v-if="indiDefined">
    <div style="display: flex">
      <indi-toggle-switch id="recording" indi-id="observers.obs_on.toggle" label-on="Recording" label-off="Off"
        class="recording spaced"></indi-toggle-switch>
      <div style="flex: 1" class="purpose">
        <div class="label-text">Purpose:</div>
        <indi-current-target indi-id="observers.obs_name"></indi-current-target>
      </div>
      <div class="current-observer">
        <div class="label-text">Current observer:</div>
        <indi-switch-dropdown indi-id="observers.observers"></indi-switch-dropdown>
      </div>
      <div v-for="(names, group) in streamNames" class="toggles spaced">
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
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

#recording {
  margin-top: $unit;
}



.observer-control {
  background: var(--bg-alternate);
}

.toggles {
  position: relative;
  display: flex;
  margin-left: $medgap;
  padding-left: 1.5rem;
  border-left: 1px solid gray;

  .label-text {
    line-height: $unit;
    display: block;
    padding: 0.5rem;
  }

  .group-label {
    position: absolute;
    left: 0;
    transform: rotate(-90deg);
    font-variant: small-caps;
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

.recording,
.purpose,
.current-observer {
  padding: 0 $medgap;
  margin-right: $medgap;
  font-size: 125%;
  line-height: 1.7em;
}


.save-path {
  font-family: monospace;
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