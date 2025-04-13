<template>
    <div class="nudger">
        <div>
            <clicky-stepper label="x" @step="nudge"></clicky-stepper>
            <clicky-stepper label="y" @step="nudge"></clicky-stepper>
        </div>
        <!-- <div class="controls">
            <button @click="nudge(1, 'x')">+x</button>
            <button @click="nudge(1, 'y')">+y</button>
            <button @click="nudge(1, 'z')">+z</button>
            <input v-model="amount.x" style="text-align: center">
            <input v-model="amount.y" style="text-align: center">
            <input v-model="amount.z" style="text-align: center">
            <button @click="nudge(-1, 'x')">-x</button>
            <button @click="nudge(-1, 'y')">-y</button>
            <button @click="nudge(-1, 'z')">-z</button>
        </div> -->
    </div>
</template>
<style scoped>
</style>
<script>
import utils from "@/mixins/utils.js";
import IndiMomentarySwitch from "@/components/indi/IndiMomentarySwitch.vue";
import ClickyStepper from "@/components/basic/ClickyStepper.vue";

export default {
    mixins: [utils],
    data: function () {
        return {amount: {x: 5, y: 5, z: 200}};
    },
    components: {IndiMomentarySwitch, ClickyStepper},
    methods: {
        nudge(payload) {
            this.indi.sendIndiNewByNames("tcsi", "pyrNudge", payload.label, payload.amount);
        },
    }
}
</script>