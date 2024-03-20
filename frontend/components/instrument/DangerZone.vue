<template>
    <div class="danger-zone view padded gap-bottom">
        <div>
            <indi-momentary-switch
                indi-id="tcsi.acqFromGuider.request"
                label="acquire from guider"
                class="acquire red"
                :disabled="!goodToAcquire"
                @click="triggerAcquireCooldown"
            ></indi-momentary-switch>
        </div>
        <div>
            <div v-if="indiIdExists('flipacq.presetName')" class="control">
            <div class="name">Acquisition mirror:</div>
            <indi-switch-multi-element class="flipacq" indi-id="flipacq.presetName" :columns="2"></indi-switch-multi-element>
            </div>
            <div v-else class="control">
                Waiting for flipacq...
            </div>
            <indi-momentary-switch indi-id="tcsi.offlF_dump.request" style="width: 100%" label="focus offload" class="dump-focus"></indi-momentary-switch>
            <scram-button></scram-button>
        </div>
        <div class="toggles">
            <div class="name">K-mirror tracking</div>
            <indi-toggle-switch class="tracking-toggle"
                indi-id="ktrack.tracking.toggle"
                :ignoreBusyState="true"></indi-toggle-switch>

            <div class="name">ADC tracking</div>
            <indi-toggle-switch class="tracking-toggle"
                indi-id="adctrack.tracking.toggle"
                :ignoreBusyState="true"></indi-toggle-switch>
            <div class="name">telescope T/T offload</div>
            <indi-toggle-switch class="tracking-toggle"
                indi-id="tcsi.offlTT_enable.toggle"
                :disabled="loopIsOpen"
                :ignoreBusyState="true"></indi-toggle-switch>
            <div class="name">camwfs-align loop</div>
            <indi-toggle-switch class="tracking-toggle"
                indi-id="camwfs-align.loop_state.toggle"
                :disabled="loopIsOpen"></indi-toggle-switch>
                
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
    
    width: 10em;
    height: 10em;
    padding: 1em;
    border-radius: 50%;
}

.dump-focus {
    // width: 7em;
    // height: 7em;
}

.control {
    padding-bottom: $unit;
}
body.dark .danger-zone.view {
    /* display: flex; */
    // text-align: center;
    display: grid;
    grid-template-columns: 1fr 2fr 3fr;
    grid-gap: $unit;
    background-color: transparentize(darken($danger-red, 40), 0.2);
}
/* .tracking-toggle {
    flex: 1;
} */
.span-two {
    grid-column: 1/3;
    button {
        width: 100%;
    }
}
.toggles {
    grid-template-columns: 1fr 1fr;
    display: grid;
    grid-gap: $medgap;
}
.name {
    // color: var(--fg-active);
    font-weight: bold;
}
</style>
<script>
import utils from "~/mixins/utils.js";
import IndiMomentarySwitch from '../indi/IndiMomentarySwitch.vue';
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiToggleSwitch from '../indi/IndiToggleSwitch.vue';
import Nudger from './Nudger.vue';
import ScramButton from './ScramButton.vue';

export default {
    mixins: [utils],
    data() {
      return {
          acquireCooldown: 0
      };  
    },
    methods: {
        coolDownTick() {
            this.acquireCooldown = this.acquireCooldown - 1;
            setTimeout(this.coolDownTick, 1000);
        },
      triggerAcquireCooldown() {
        this.acquireCooldown = 6;
        setTimeout(this.coolDownTick, 1000);
      }  
    },
    computed: {
        loopIsOpen() {
            return this.retrieveValueByIndiId('holoop.loop_state.toggle') == 'Off';
        },
        goodToAcquire() {
            return this.retrieveValueByIndiId('flipacq.presetName.in') == 'On' && this.acquireCooldown == 0;
        }
    },
    components: {
        IndiToggleSwitch,
        IndiMomentarySwitch,
        IndiSwitchMultiElement,
        Nudger,
        ScramButton
    },
}
</script>