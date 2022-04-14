<template>
    <div class="offloading view padded gap-bottom">
        <indi-momentary-switch indi-id="tcsi.acqFromGuider.request" label="acquire from guider" class="acquire control"></indi-momentary-switch>
        <div v-if="indiIdExists('flipacq.position')" class="control">
          <div class="name">Acquisition mirror:</div>
          <indi-switch-multi-element class="flipacq" indi-id="flipacq.position" orientation="vertical"></indi-switch-multi-element>
        </div>
        <div v-else class="control">
            Waiting for flipacq...
        </div>
        <div class="control">
            <div class="name">K-mirror tracking</div>
            <indi-toggle-switch class="tracking-toggle"
                indi-id="ktrack.tracking.toggle"
                :ignoreBusyState="true"></indi-toggle-switch>
        </div>
        <div class="control">
            <div class="name">ADC tracking</div>
            <indi-toggle-switch class="tracking-toggle"
                indi-id="adctrack.tracking.toggle"
                :ignoreBusyState="true"></indi-toggle-switch>
        </div>
        <div class="control">
            <div class="name">telescope T/T offload</div>
            <indi-toggle-switch class="tracking-toggle"
                indi-id="tcsi.offlTT_enable.toggle"
                :ignoreBusyState="true"></indi-toggle-switch>
        </div>
    </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
.flipacq {
    .buttons.minigrid {
        grid-template-columns: 1fr 1fr;
    }
}
.acquire {
    background: var(--btn-warn-bg-gradient);
    width: 7em;
    height: 7em;
    padding: 1em;
}
.control {
    padding-bottom: $unit;
}
.offloading {
    /* display: flex; */
    text-align: center;
}
/* .tracking-toggle {
    flex: 1;
} */
.name {
    color: var(--fg-active);
    font-weight: bold;
}
</style>
<script>
import utils from "~/mixins/utils.js";
import IndiMomentarySwitch from '../indi/IndiMomentarySwitch.vue';
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiToggleSwitch from '../indi/IndiToggleSwitch.vue';

export default {
    mixins: [utils],
    components: {
        IndiToggleSwitch,
        IndiMomentarySwitch,
        IndiSwitchMultiElement,
    },
    methods: {
    }
}
</script>