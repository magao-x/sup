<template>
  <div>
    <indi-property
      indi-id="timeSeriesSimulator.gizmo_0000"
    ></indi-property>
    <indi-property
      indi-id="timeSeriesSimulator.gizmo_0001"
    ></indi-property>
    <toggle-switch v-model="dingus"></toggle-switch>
    <select><option>Foo</option><option>Foo</option></select>
    <br><br>
    <indi-switch-multi-element indi-id="timeSeriesSimulator.function"></indi-switch-multi-element>
    <indi-switch-multi-element indi-id="fwpupil.filterName"></indi-switch-multi-element>
    <indi-switch-multi-element indi-id="fliptip.position"></indi-switch-multi-element>
    <div style="width: 10em;">
      <div class="btn active">Foo</div>
    </div>
    <div style="width: 10em;">
      <button>Button</button>
    </div>
  </div>
</template>
<style scoped lang="scss">
@import "./css/variables.scss";
select {
  border: 1px solid $primary;
  background: $base03;
  line-height: inherit;
  color: $base0;
  font-size: 1em;
}
// * {
//     border: 1px solid;
// }
// .controls-groups {
//   display: flex;
//   & > * {
//     flex: 1;
//     border: 1px solid $base00;
//     margin: $unit;
//   }
// }
// .sideBySide {
//   display: flex;
//   .left {
//     flex: 1;
//   }
//   .right {
//     flex: 1;
//   }
// }
// .adjustableIncrement {
//   text-align: right;
//   .buttons {
//     height: 1em;
//     display: flex;
//     button,
//     .btn {
//       flex: 1;
//     }
//     input {
//       margin: 0;
//       padding: 0;
//       height: auto;
//       width: 2em;
//       background-color: inherit;
//       color: inherit;
//     }
//   }
//   input.adjustable {
//     flex: 1;
//     width: 100%;
//   }
// }
</style>
<script>
import CameraControlsGroup from "~/components/instrument/CameraControlsGroup.vue";
import BenchView from "~/components/instrument/BenchView.vue";
import AdjustableNumberStepper from "~/components/basic/AdjustableNumberStepper.vue";
import RegionOfInterest from "~/components/instrument/RegionOfInterest.vue";
import ToggleSwitch from "~/components/basic/ToggleSwitch.vue";
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiElement from "~/components/indi/IndiElement.vue";
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import utils from "~/mixins/utils.js";

const components = {
  CameraControlsGroup,
  BenchView,
  AdjustableNumberStepper,
  RegionOfInterest,
  ToggleSwitch,
  IndiElement,
  IndiSwitchMultiElement,
  IndiProperty
};

export default {
  components,
  data: function () {
    return {components, dingus: false};
  },
  computed: {
    amplitude: function () {
      let elt = this.$root.retrieveByIndiId('timeSeriesSimulator.duty_cycle.amplitude');
      if (elt !== null) {
        return elt.value;
      } else {
        return null;
      }
    }
  }
};
</script>