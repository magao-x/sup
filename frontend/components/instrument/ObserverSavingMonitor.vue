<template>
  <div class="observer-saving-monitor" :class="{'active': isSaving}">
    <span class="save-path">
      /data/obs/{{ semester }}/{{ currentObserverEmail }}/{{ folderTimeStamp }}_*_<indi-value indi-id="observers.obs_name.current"></indi-value>/{{ enabledCamerasShellSnippet }}
    </span>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
.observer-saving-monitor { 
    background: var(--bg-alternate);
    transition: background 1s;
    &.active {
        background: $plasma-blue;
        color: var(--fg-normal);
    }
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
import IndiSwitchDropdown from "../indi/IndiSwitchDropdown.vue";
import IndiToggleSwitch from "../indi/IndiToggleSwitch.vue";
import AlternateIndiToggleSwitch from "../indi/AlternateIndiToggleSwitch.vue";
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
  mixins: [indi, utils],
  components: {
    IndiValue,
    IndiSwitchMultiElement,
    IndiSwitchDropdown,
    IndiToggleSwitch,
    IndiElement,
    IndiProperty,
    AlternateIndiToggleSwitch
  },
  computed: {
    currentObserverEmail() {
      let prop = this.retrieveByIndiId("observers.observers");
      if (!prop) return;
      console.log(prop._elements);
        for (let elementKey of Object.keys(prop._elements)) {
          if (prop._elements[elementKey]._value == 'On') {
            return prop._elements[elementKey].label;
          }
      }
    },
    isSaving() {
      return this.retrieveByIndiId("observers.obs_on.toggle")?._value == 'On';
    },
    enabledCameras() {
      let currentCameras = [];
      for (let camName of this.camNames) {
        const isEnabled = this.retrieveValueByIndiId(`observers.writers.cam${camName}`) == 'On';
        if (isEnabled) {
            currentCameras.push(`cam${camName}`);
        }
        
      }
      return currentCameras;
    },
    enabledCamerasShellSnippet() {
        if (this.enabledCameras.length == 0) return '';
        let snippet = '{';
        for (let fullCamName of this.enabledCameras) {
            snippet += fullCamName + ',';
        }
        
        if (this.enabledCameras.length == 1) { 
            snippet = snippet.slice(1, -1);
        } else {
            snippet = snippet.slice(0, -1) + '}';
        }
        return snippet;
    },
    semester() {
      return this.scheduleSemester(this.time.currentTime);
    },
    folderTimeStamp() {
      return this.time.currentTime.toFormat('yyyy-MM-dd');
    },
    catalogObject() {
      let elem = this.retrieveByIndiId("tcsi.catalog.object");
      if (!elem) return null;
      return elem._value;
    },
  },
};
</script>