<template>
  <div class="danger-zone">
    <div style="text-align: center; position: relative">
      <!-- indi-id="tcsi.acqFromGuider.request"  -->
      <button v-if="readyToAcquire" class="cancel" @click="cancelAcquire">cancel</button>
      <button v-else class="prepare red" :disabled="!goodToAcquire" @click="prepareToAcquire">{{ prepareButtonLabel }}</button>
      <button v-if="readyToAcquire" 
        class="red acquire" :disabled="!goodToAcquire" @click="triggerAcquire">acquire</button>
    </div>
    <div>
      <div v-if="indiIdExists('flipacq.presetName')" class="control">
        
      </div>
      <div v-else class="control">
        Waiting for flipacq...
      </div>
      <button style="width: 100%" @click="triggerOffset" :disabled="!goodToOffset">{{ maybeFocusOffset }}</button>
      <indi-momentary-switch indi-id="tcsi.offlF_dump.request" style="width: 100%" label="focus dump"
        class="dump-focus"></indi-momentary-switch>
      <scram-button></scram-button>
    </div>
    <div class="toggles span-two">
      <div class="name">Acquisition mirror:</div>
      <indi-switch-multi-element class="tracking-toggle" indi-id="flipacq.presetName"
        :columns="2"></indi-switch-multi-element>
      <div class="name">K-mirror tracking</div>
      <indi-toggle-switch class="tracking-toggle" indi-id="ktrack.tracking.toggle"
        :ignoreBusyState="true"></indi-toggle-switch>

      <div class="name">ADC tracking</div>
      <indi-toggle-switch class="tracking-toggle" indi-id="adctrack.tracking.toggle"
        :ignoreBusyState="true"></indi-toggle-switch>
      <div class="name">telescope T/T offload</div>
      <indi-toggle-switch class="tracking-toggle" indi-id="tcsi.offlTT_enable.toggle"
        :ignoreBusyState="true"></indi-toggle-switch>
      <div class="name">pupil tracking</div>
      <indi-toggle-switch class="tracking-toggle" indi-id="camwfs-align.loop_state.toggle"></indi-toggle-switch>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@use "sass:color";
@use "./css/variables.scss" as *;

.flipacq {
  .buttons.minigrid {
    grid-template-columns: 1fr 1fr;
  }
}

.prepare, .acquire, .cancel {
  border-radius: 50%;
}

button { 
  text-align: center;
}

.acquire {
  width: 5em;
  height: 5em;
  position: absolute;
  left: -0.5rem;
  bottom: -0.5rem;
  padding: 0;
}

.prepare, .cancel {
  width: 10em;
  height: 10em;
  padding: 1.5em;
  position: absolute;
  top: 0;
  left: 0;
}

.cancel {
  padding-left: 2em;
  padding-right: 0;
  padding-top: 0;
  padding-bottom: 1em;
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
  grid-template-columns: 1fr 1fr;
  grid-gap: $unit;
  background-color: color.scale(color.adjust($danger-red, $lightness: 10%), $alpha: -20%);
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
import IndiMomentarySwitch from '~/components/indi/IndiMomentarySwitch.vue';
import IndiSwitchMultiElement from "~/components/indi/IndiSwitchMultiElement.vue";
import IndiToggleSwitch from '~/components/indi/IndiToggleSwitch.vue';
import Nudger from './Nudger.vue';
import ScramButton from './ScramButton.vue';

export default {
  mixins: [utils],
  data() {
    return {
      acquireCooldown: 0,
      focusCooldown: 0,
      readyToAcquire: false,
    };
  },
  methods: {
    acquireCooldownTick() {
      this.acquireCooldown = Math.max(this.acquireCooldown - 1, 0);
      if (this.acquireCooldown > 0) {
        setTimeout(this.acquireCooldownTick, 1000);
      }
    },
    focusCooldownTick() {
      this.focusCooldown = Math.max(this.focusCooldown - 1, 0);
      if (this.focusCooldown > 0) {
        setTimeout(this.focusCooldownTick, 1000);
      }
    },
    triggerAcquire() {
      // this.indi.sendIndiNewByNames("maggieo_x", "mute", "toggle", "On");
      this.readyToAcquire = false;
      this.acquireCooldown = 6;
      setTimeout(this.acquireCooldownTick, 1000);
      this.indi.sendIndiNewByNames("tcsi", "acqFromGuider", "request", "On");
    },
    prepareToAcquire() {
      this.readyToAcquire = true;
    },
    cancelAcquire() {
      this.readyToAcquire = false;
    },
    triggerOffset() {
      this.focusCooldown = 6;
      setTimeout(this.focusCooldownTick, 1000);
      this.indi.sendIndiNewByNames("tcsi", "pyrNudge", "z", 1400);
    },
  },
  computed: {
    loopIsOpen() {
      return this.retrieveValueByIndiId('holoop.loop_state.toggle') == 'Off';
    },
    prepareButtonLabel() {
      if (this.acquireCooldown > 0) {
        return `wait ${this.acquireCooldown} sec`;
      } else if (this.retrieveValueByIndiId('flipacq.presetName.in') !== 'On') {
        return "insert flipacq to acquire";
      } else {
        return "prepare to acquire";
      }
    },
    goodToAcquire() {
      return (
        this.retrieveValueByIndiId('flipacq.presetName.in') == 'On' 
        &&
        this.acquireCooldown == 0
      );
    },
    goodToOffset() {
      return (
        this.retrieveValueByIndiId('flipacq.presetName.in') == 'On'
        &&
        this.focusCooldown == 0
      );
    },
    maybeFocusOffset() {
      if (this.goodToOffset) {
        return "apply focus offset";
      } else if (this.focusCooldown > 0) {
        return `wait ${this.focusCooldown} sec`;
      } else {
        return "insert flipacq to offset focus";
      }
    },
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