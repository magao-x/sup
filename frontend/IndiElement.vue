<template>
    <div>
        <span v-if="property.perm != 'ro'">
            <label :for="dottedName">{{ dottedName }}={{ element.value }}</label>
            <button @click="populate">load &rarr;</button>
            <input :id="dottedName" v-model.trim="userInput">
            <button @click="send">send</button>
        </span><span v-if="property.perm == 'ro'">
            {{ dottedName }}={{ element.value }}
        </span>
    </div>
</template>
<style scoped>

</style>
<script>
export default {
    props: ["device", "property", "element"],
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
            userInput: ""
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
        }
    }
}
</script>
