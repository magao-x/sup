<template>
  <div class="observer-control cols view">
    <div class="col">
        <div>Current observer: <indi-value indi-id="observers.current_observer.pfoa"></indi-value></div>
        <div>Full name: <indi-value indi-id="observers.current_observer.full_name"></indi-value></div>
        <div>Institution: <indi-value indi-id="observers.current_observer.institution"></indi-value></div>
        <div>Email:<indi-switch-dropdown indi-id="observers.observers"></indi-switch-dropdown></div>
    </div>
    <div class="col">
        <div style="font-size: 125%; text-align: center"><indi-toggle-switch indi-id="observers.obs_on.toggle" label-on="Record" label-off="Off" :prompt="true"></indi-toggle-switch></div>
        <div>Observation name: <indi-value indi-id="observers.obs_name.current"></indi-value></div>
        <div> <indi-element indi-id="observers.obs_name.target"></indi-property>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';

.observer-control {
    display: flex;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiSwitchDropdown from '../indi/IndiSwitchDropdown.vue';
import IndiToggleSwitch from '../indi/IndiToggleSwitch.vue';
import IndiElement from '../indi/IndiElement.vue';
import IndiProperty from "~/components/indi/IndiProperty.vue";

export default {
  props: {
      device: {
      type: String,
      default: "observers"
    }
  },
  mixins: [indi],
  components: {
    IndiValue,
    IndiSwitchMultiElement,
    IndiSwitchDropdown,
    IndiToggleSwitch,
    IndiElement,
    IndiProperty
  },
  computed: {
  }
};
</script>