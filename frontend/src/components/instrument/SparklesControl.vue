<template>
    <div v-if="indiDefined" class=" view padded gap-bottom">
        <div class="col" style="text-align: center">
            <div style="margin-bottom: 5px;">
                <finite-state-machine-status
                  :device="thisDevice"></finite-state-machine-status>
                ✨
            </div>
            <div>
                <indi-momentary-switch
                    indi-id="tweeterSpeck.zero.request" label="Ø" class="zero-sparkles"></indi-momentary-switch>
                <indi-toggle-switch indi-id="tweeterSpeck.modulating.toggle" label-on="sparkle"></indi-toggle-switch>
            </div>
        </div>
        <div class="row">
            <div class="label">Angle (º):</div>
            <indi-current-target 
                indi-id="tweeterSpeck.angle"></indi-current-target>
        </div>
        <div class="row">
            <div class="label">Amplitude:</div>
            <indi-current-target
                indi-id="tweeterSpeck.amp"></indi-current-target>
        </div>
        
        <div class="row">
            <div class="label">Separation (&lambda;/D):</div>
            <indi-current-target 
                indi-id="tweeterSpeck.separation"></indi-current-target>
        </div>
        
    </div>
    <div v-else class="view padded gap-bottom">
        Waiting for sparkles...
    </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.full-width {
    width: 100%;
}
.cols {
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
}

.row {
    display: grid;
    align-items: stretch;
    grid-template-columns: 1fr 2fr;
}

.zero-sparkles {
    border-radius: 100%;
    width: 2 * $unit;
    height: 2 * $unit;
    text-align: center;
}
</style>
<script>
import IndiMomentarySwitch from '@/components/indi/IndiMomentarySwitch.vue';
import IndiProperty from '@/components/indi/IndiProperty.vue';
import IndiCurrentTarget from '@/components/indi/IndiCurrentTarget.vue';
import IndiToggleSwitch from '@/components/indi/IndiToggleSwitch.vue';
import IndiValue from '@/components/indi/IndiValue.vue';
import FiniteStateMachineStatus from "@/components/instrument/FiniteStateMachineStatus.vue";
import indi from "@/mixins/indi.js";
import utils from "@/mixins/utils.js";

export default {
    props: ["device", "indiId"],
    mixins: [indi, utils],
    inject: ["indi"],
    components: {
        IndiMomentarySwitch,
        IndiToggleSwitch,
        IndiProperty,
        FiniteStateMachineStatus,
        IndiValue,
        IndiCurrentTarget,
    },
    computed: {
        isTriggered() {
            return this.thisDevice["trigger"]._elements["toggle"]._value == "On";
        },
        isSparkling() {
            return this.thisDevice["modulating"]._elements["toggle"]._value == "On";
        },
        currentFPS() {
            return this.retrieveValueByIndiId("fxngensync.C1freq.current");
        }
    }
}
</script>