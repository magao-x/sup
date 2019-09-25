<template>
    <div class="element">
        <button class="restore" :disabled="isDisabled" @click="populate"><i class="material-icons">sync</i></button>
        <number-input
            v-if="property.kind == 'num'"
            :min="element.min"
            :max="element.max"
            :step="stepFromFormat(element.format, element.step)"
            v-model="userInput"
            :disabled="isDisabled"
        ></number-input>
        <input
        v-else
            :id="dottedName"
            v-model.trim="userInput"
            :disabled="isDisabled">
        <button class="commit" :disabled="isDisabled" @click="send"><i class="material-icons">done</i></button>
    </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';

.element {
    display: flex;
}
input {
    flex: 1;
    width: $unit;
    min-width: $unit;
}
</style>
<script>
import NumberInput from "./NumberInput.vue";
import utils from "./utils.js";

export default {
    props: ["device", "property", "element"],
    components: {
        NumberInput
    },
    mixins: [utils],
    methods: {
        populate: function () {
            this.userInput = this.element.value;
        },
        send: function () {
            this.$socket.emit('indi_new', {
                'device': this.device.name,
                'property': this.property.name,
                'element': this.element.name,
                'value': this.userInput
            })
        }
    },
    data: function () {
        return {
            userInput: this.element.value
        }
    },
    computed: {
        dottedName: function () {
            return this.device.name + "." + this.property.name + "." + this.element.name;
        },
        displayName: function () {
            if (this.element.label !== null) {
                return this.element.label;
            } else {
                return this.dottedName;
            }
        },
        isPairedCurrent: function () {
            if (this.element.name === "current" && this.property.elements.hasOwnProperty("target")) {
                return true;
            }
            return false;
        },
        isDisabled: function () {
            return this.property.perm == 'ro' || this.isPairedCurrent;
        }
    }
}
</script>
