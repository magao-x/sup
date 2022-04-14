<template>
    <div class="nudger">
        <div>Nudger</div>
        <div>
            <clicky-stepper></clicky-stepper>
        </div>
        <div class="controls">
            <button @click="nudge(1, 'x')">+x</button>
            <button @click="nudge(1, 'y')">+y</button>
            <button @click="nudge(1, 'z')">+z</button>
            <input v-model="amount.x" style="text-align: center">
            <input v-model="amount.y" style="text-align: center">
            <input v-model="amount.z" style="text-align: center">
            <button @click="nudge(-1, 'x')">-x</button>
            <button @click="nudge(-1, 'y')">-y</button>
            <button @click="nudge(-1, 'z')">-z</button>
        </div>
    </div>
</template>
<style scoped>
.controls {
    font-size: 150%;
    display: grid;
    grid-template-columns: 3em 3em 3em;
}
input.xy {
    grid-column: 1 / 3;
}
/* .side {
    display: flex;
    flex-direction: column;
}
.side.z button, .side.z input {
    display: block;
} */
</style>
<script>
import utils from "~/mixins/utils.js";
import IndiMomentarySwitch from "~/components/indi/IndiMomentarySwitch.vue";
import ClickyStepper from "~/components/basic/ClickyStepper.vue";

export default {
    mixins: [utils],
    data: function () {
        return {amount: {x: 5, y: 5, z: 200}};
    },
    components: {IndiMomentarySwitch, ClickyStepper},
    methods: {
        nudge(sign, direction) {
            this.sendIndiNewByNames("tcsi", "pyrNudge", direction, sign * this.amount[direction]);
        },
    }
}
</script>