<template>
    <div v-if="indiDefined" class="cols view padded gap-bottom">
        <div>
            <div style="font-size: 150%; text-align: center;">✨ <finite-state-machine-status
                  :device="thisDevice"></finite-state-machine-status></div>
            <indi-toggle-switch indi-id="tweeterSpeck.modulating.toggle" class="full-width" label-on="sparkle"></indi-toggle-switch>
        </div>
        <div class="col">
            <div>Frequency (Hz):</div>
            <indi-property
                v-if="!isTriggered"
                :disabled="isSparkling"
                indi-id="tweeterSpeck.frequency"></indi-property>
            <input v-else
                :value="currentFPS"
                disabled>
        </div>
        <div class="col">
            <div>Angle (º):</div>
            <indi-property 
                v-if="!isSparkling"
                indi-id="tweeterSpeck.angle"></indi-property>
            <input v-else
                :value="retrieveValueByIndiId('tweeterSpeck.angle.current')"
                disabled>
        </div>
        <div>
            <div>Amplitude:</div>
            <indi-property
                v-if="!isSparkling"
                indi-id="tweeterSpeck.amp"></indi-property>
            <input v-else
                :value="retrieveValueByIndiId('tweeterSpeck.amp.current')"
                disabled>
        </div>
        
        <div>
            <div>Separation (&lambda;/D):</div>
            <indi-property 
                v-if="!isSparkling"
                indi-id="tweeterSpeck.separation"></indi-property>
            <input v-else
                :value="retrieveValueByIndiId('tweeterSpeck.separation.current')"
                disabled>
        </div>
        <div>
            <indi-toggle-switch
                :read-only="isSparkling"
                indi-id="tweeterSpeck.trigger.toggle" class="full-width" label-on="trigger"></indi-toggle-switch>
            <indi-momentary-switch
                :disabled="isSparkling"
                indi-id="tweeterSpeck.zero.request" class="full-width" label="zero"></indi-momentary-switch>
        </div>
    </div>
    <div v-else>
        Waiting for sparkles...
    </div>
</template>
<style lang="scss" scoped>
.full-width {
    width: 100%;
}
.cols {
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
}
</style>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiMomentarySwitch from '~/components/indi/IndiMomentarySwitch.vue';
import IndiToggleSwitch from '~/components/indi/IndiToggleSwitch.vue';
import IndiValue from '~/components/indi/IndiValue.vue';
import IndiProperty from '~/components/indi/IndiProperty.vue';
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";

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
    },
    computed: {
        isTriggered() {
            return this.thisDevice["trigger"]._elements["toggle"]._value == "On";
        },
        isSparkling() {
            return this.thisDevice["modulating"]._elements["toggle"]._value == "On";
        },
        currentFPS() {
            return this.retrieveValueByIndiId("camwfs.fps.current");
        }
    }
}
</script>