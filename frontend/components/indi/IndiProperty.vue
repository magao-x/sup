<template>
  <div v-if="thisDevice && thisProperty" class="property">
    <p v-if="thisProperty.message !== null">{{ thisProperty.message }}</p>
    <template v-if="thisProperty._kind == 'swt'">
      <indi-switch-multi-element :device="thisDevice" :property="thisProperty"></indi-switch-multi-element>
    </template>
    <template v-else>
      <div
        v-if="isPairedCurrentTarget"
        class="paired-current-target">
        <cancel-button
        :disabled="!isEditing"
        @cancel="doneEditing"
        ></cancel-button>
        <indi-element
          :forceDisabled="!isEditing"
          class="target"
          :device="thisDevice"
          :property="thisProperty"
          :element="eitherCurrentOrTarget"
          @commit="doneEditing"
          @click="beginEditing"
          ref="indiElement"
        ></indi-element>
        <edit-button
          v-if="!isEditing"
          :disabled="isDisabled"
          @edit="beginEditing"
        ></edit-button>
      </div>
      <indi-element
        v-else
        v-for="elem in objectAsSortedArray(thisProperty._elements)"
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
@use "./css/variables.scss" as *;

.paired-current-target {
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
import EditButton from "~/components/basic/EditButton.vue";
import CommitButton from "~/components/basic/CommitButton.vue";
import CancelButton from "~/components/basic/CancelButton.vue";
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
    IndiValue,
    EditButton,
    CancelButton,
    CommitButton,
  },
  props: ["device", "property", "indiId", "disabled"],
  mixins: [indi, utils],
  methods: {
    beginEditing() {
      this.isEditing = true;
      this.$nextTick(() => {
        this.$refs.indiElement.$el.querySelector('input').focus();
      })
    },
    doneEditing() {
      this.isEditing = false;
    }
  },
  data() {
    return {
      isEditing: false,
    };
  },
  computed: {
    isPairedCurrentTarget: function() {
      if (
        this.indiDefined &&
        this.thisProperty._elements.target !== undefined &&
        this.thisProperty._elements.current !== undefined
      ) {
        return true;
      }
      return false;
    },
    isDisabled() {
      return !this.indiDefined || this.disabled || this.thisProperty.perm == 'ro';
    },
    eitherCurrentOrTarget() {
      if (this.isPairedCurrentTarget) {
        if (this.isEditing) {
          return this.thisProperty._elements.target;
        } else {
          return this.thisProperty._elements.current;
        }
      }
    }
  }
};
</script>
