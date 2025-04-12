<template>
    <div class="property" v-if="indiDefined">
      {{ prefix }}
      <input
        :disabled="isDisabled"
        :value="currentValueOrInput"
        @focus="beginEditing"
        @blur="maybeCancelEditing"
        @input="updateUserInput"
        @keydown.enter="commit"
        @keydown.escape="cancelEditing"
        ref="control"
        :style="styles"
      >
      {{ suffix }}
      <commit-button v-if="indiDefined && !hideCommitButton" :disabled="!isEditing" @commit="commit"></commit-button>
      {{ note }}
    </div>
    <div v-else>Waiting for property</div>
  </template>
  <style lang="scss" scoped>
  @use "./css/variables.scss" as *;
  input {
    flex: 1
  }
  .property {
    display: inline-flex;
  }
  </style>
  <script>

  import indi from "~/mixins/indi.js";
  import utils from "~/mixins/utils.js";
  import CommitButton from "~/components/basic/CommitButton.vue";

  export default {
    mixins: [indi, utils],
    props: {
      indiId: String,
      disabled: Boolean,
      hideCommitButton: {
        type: Boolean,
        default: false,
      },
      width: {
        type: String,
        default: null,
      },
      prefix: {
        type: String,
        default: ""
      },
      suffix: {
        type: String,
        default: "",
      },
      note: {
        type: String,
        default: "",
      },
      format: {
        type: String,
        default: null,
      }
    },
    // ["indiId", "disabled", "hideCommitButton", "width"],
    components: {
      CommitButton
    },
    methods: {
      updateUserInput: function (payload) {
        this.userInput = payload.target.value;
      },
      beginEditing: function () {
        if (this.isDisabled) {
          return;
        }
        this.userInput = this.currentValue;
        this.isEditing = true;
      },
      cancelEditing: function () {
        if (this.isDisabled) {
          return;
        }
        this.userInput = null;
        this.isEditing = false;
      },
      maybeCancelEditing() {
        if (this.currentValue == this.userInput) {
          this.cancelEditing();
        }
      },
      commit: function () {
        console.log("Commit!");
        if (this.currentValue == this.userInput) {
          console.log("No changes")
        } else {
          this.sendIndiNew(
            this.thisProperty,
            this.thisProperty._elements.target,
            this.userInput
          );
        }
        this.isEditing = false;
        this.$refs.control.blur();
      },
    },
    data() {
      return {
        userInput: null,
        isEditing: false,
      };
    },
    computed: {
      styles() {
        if (this.width) {
          return {width: this.width};
        }
        return {};
      },
      isDisabled() {
        return !this.indiDefined || this.disabled || !this.thisProperty || this.thisProperty.perm == 'ro';
      },
      currentValue: function () {
        if (!this.thisProperty) { return null; }
        let current = this.thisProperty._elements.current;
        if (this.thisProperty._kind == 'num') {
          if (this.format) {
            return this.applyFormatString(this.format, current._value);
          } else if (current.format) {
            return this.applyFormatString(current.format, current._value);
          } else {
            return String(current._value);
          }
        } else {
          return current._value;
        }
      },
      currentValueOrInput: function () {
        if (this.isEditing) {
          return this.userInput;
        } else {
          return this.currentValue;
        }
      },
    }
  };
  </script>
  