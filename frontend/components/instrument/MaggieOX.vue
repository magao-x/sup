<template>
  <div>
    <div style="display: flex">
      <div>Maggie-o X:</div>
      <indi-switch-multi-element indi-id="maggieo_x.personality"></indi-switch-multi-element>
      <indi-momentary-switch indi-id="maggieo_x.reload_personality.request"
        label="reload personality"></indi-momentary-switch>
      <indi-toggle-switch indi-id="maggieo_x.mute.toggle" label-on="muted" label-off="unmuted"></indi-toggle-switch>
    </div>
    <div>
      <div>Speak: <indi-current-target indi-id="maggieo_x.speech_text"></indi-current-target></div>
      
      <indi-momentary-switch indi-id="maggieo_x.speak.request"
        label="speak"></indi-momentary-switch>
    </div>
    <indi-switch-multi-element indi-id="maggieo_x.soundboard" :columns="6"></indi-switch-multi-element>
  </div>
</template>
<script>
import utils from "~/mixins/utils.js";
import IndiElement from "../indi/IndiElement.vue";
import IndiValue from "../indi/IndiValue.vue";
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiCurrentTarget from "~/components/indi/IndiCurrentTarget.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiToggleSwitch from "~/components/indi/IndiToggleSwitch.vue";
import IndiMomentarySwitch from "~/components/indi/IndiMomentarySwitch.vue";

export default {
  mixins: [utils],
  inject: ["indi"],
  components: {
    IndiValue,
    IndiElement,
    IndiProperty,
    IndiCurrentTarget,
    IndiSwitchMultiElement,
    IndiToggleSwitch,
    IndiMomentarySwitch,
  },
};
</script>