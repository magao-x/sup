<template>
  <div class="observer-control" :class="{ 'active': isObserving }" v-if="indiDefined">
    <div style="display: flex">
      <indi-toggle-switch indi-id="observers.obs_on.toggle" label-on="Recording" label-off="Off" class="recording margin-right"></indi-toggle-switch>
      <div style="flex: 1" class="margin-right">
        Purpose:
        <indi-current-target indi-id="observers.obs_name"></indi-current-target>
      </div>
      <div style="flex: 1" class="margin-right">
        Current observer:
        <indi-switch-dropdown indi-id="observers.observers"></indi-switch-dropdown>
      </div>
      <div v-for="(names, group) in streamNames" class="toggles" style="display: flex; text-align: center">
        <span class="group-label">{{ group }}</span>
        <alternate-indi-toggle-switch v-for="name in names" :indi-id="`observers.writers.${name}`" :label="name"
          :disabled="isObserving" class="stream"></alternate-indi-toggle-switch>
        <!-- <span v-else-if="retrieveValueByIndiId(`${name}-sw.writing.toggle`) == 'On'" class="glowy stream">
          {{ name }}
          <material-icon name="power_settings_new"></material-icon>
        </span>
        <span v-else class="notGlowy stream">
          {{ name }}
          <material-icon name="link_off"></material-icon>
        </span> -->
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.observer-control {
  background: var(--bg-alternate);
}

.toggles {
  position: relative;
  padding-top: 1rem;
  padding-left: 2rem;
  border-top: 1px solid gray;
  border-left: 1px solid gray;

  .group-label {
    position: absolute;
    left: 0;
    transform: rotate(-90deg);
    font-variant: small-caps;
  }

  label {
    span {
      display: block
    }

    input {
      display: block;
      margin: 0 auto;
    }
  }
}

.margin-right {
  margin-right: 1rem;
}

span.stream {
  margin-right: 0.2rem;
}


// .glowy {
//   text-shadow: 0 0 5 $plasma-blue; /* Initial shadow */
//   animation: pulse 1s infinite alternate; /* Animation */
//   color: $plasma-blue;
// }
// .notGlowy {
//   color: $icon-gray;
// }


.cols {
  grid-template-columns: 1fr 1fr 1fr;
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
  padding: $medgap 0;
  margin-right: $medgap;
}

.purpose {
  font-size: 125%;
  display: flex;
}

.writing-toggles {
  display: flex;
  text-align: center;
  width: 100%;

  .cam-toggle {
    flex: 1;
  }
}

.current-observer {
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