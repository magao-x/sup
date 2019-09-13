<template>
    <div class="element">
        <button class="sync" :disabled="isDisabled" @click="populate"><i class="material-icons">sync</i></button>
        <number-input
            v-if="property.kind == 'num'"
            :min="element.min"
            :max="element.max"
            :step="element.step"
            v-model="userInput"
            :disabled="isDisabled"
        ></number-input>
        <input
        v-else
            :id="dottedName"
            v-model.trim="userInput"
            :disabled="isDisabled">
        <button :disabled="isDisabled" @click="send"><i class="material-icons">done</i></button>
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
.sync:enabled {
    background: $violet;
}
</style>
<script>
import NumberInput from "./NumberInput.vue";

export default {
    props: ["device", "property", "element"],
    components: {
        NumberInput
    },
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
