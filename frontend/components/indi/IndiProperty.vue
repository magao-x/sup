<template>
  <div v-if="thisDevice && thisProperty" class="property">
    <p v-if="thisProperty.message !== null">{{ thisProperty.message }}</p>
    <template v-if="thisProperty.kind == 'swt'">
      <indi-switch-multi-element :device="thisDevice" :property="thisProperty"></indi-switch-multi-element>
    </template>
    <template v-else>
      <div
        v-if="isPairedCurrentTarget"
        class="paired-current-target">
        <indi-value
          class="current"
          :device="thisDevice"
          :property="thisProperty"
          :element="thisProperty.elements.current"
        ></indi-value>
        <indi-element
          class="target"
          :device="thisDevice"
          :property="thisProperty"
          :element="thisProperty.elements.target"
        ></indi-element>
      </div>
      <indi-element
        v-else
        v-for="elem in objectAsSortedArray(thisProperty.elements)"
        :key="elem.name"
        :device="thisDevice"
        :property="thisProperty"
        :element="elem"
      ></indi-element>
    </template>
  </div>
  <div v-else>Waiting for property</div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.paired-current-target {
  max-width: 20em;
  display: flex;
  align-items: baseline;
  .current, .target {
    flex: 1;
  }
  .current {
    height: 3 * $unit;
  }
}
</style>
<script>
import IndiElement from "./IndiElement.vue";
import IndiStateIndicator from "./IndiStateIndicator.vue";
import IndiValue from "./IndiValue.vue";
import IndiSwitchMultiElement from "./IndiSwitchMultiElement.vue";
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";

export default {
  mixins: [indi, utils],
  components: {
    IndiElement,
    IndiSwitchMultiElement,
    IndiStateIndicator,
    IndiValue
  },
  props: ["device", "property", "indiId"],
  mixins: [indi, utils],
  computed: {
    isPairedCurrentTarget: function() {
      if (
        this.thisProperty.elements.target !== undefined &&
        this.thisProperty.elements.current !== undefined
      ) {
        return true;
      }
      return false;
    }
  }
};
</script>
