<template>
  <div class="adaptive-optics-loop" v-if="retrieveByIndiId(wfs)">
    <div>{{ wfs }} <finite-state-machine-status :indi-id="wfs"></finite-state-machine-status></div>
    <div><loop-state :indi-id="device"></loop-state></div>
    <div class="plot" v-if="gains">
      <plot-component :fixedYDomain="[0, 1.25]" :data="gains.plotData" :dataColors="dataColors"
        :legend="false"></plot-component>
      <div>{{ gains.nModesClosed }} modes at {{ applyFormatString("%.1f",
        retrieveValueByIndiId(`${this.wfs}.fps.current`)) }} Hz</div>
      <div v-if="retrieveByIndiId(`${this.wfs}.emgain`)">EM gain: {{ retrieveValueByIndiId(`${this.wfs}.emgain.current`)
      }}</div>
    </div>
    <div class="plot" v-else>Waiting for {{ gainCtrlDevice }}...</div>
  </div>
</template>
<style lang="scss">
@use "@/css/variables.scss" as *;

.adaptive-optics-loop {
  grid-template-columns: subgrid;
  display: grid;

  .plot {
    grid-column: 1/4;
  }
}
</style>
<script>
import indi from "@/mixins/indi.js";
import constants from "@/components/plots/constants.js";
import utils from "@/mixins/utils.js";
import PlotComponent from "@/components/plots/PlotComponent.vue";
import FiniteStateMachineStatus from '@/components/instrument/FiniteStateMachineStatus.vue';
import LoopState from '@/components/instrument/LoopState.vue';

export default {
  props: {
    device: {
      type: String,
    },
    gainCtrlDevice: {
      type: String,
    },
    plotColor: { type: String },
    wfs: {
      type: String,
    },
    otherDevices: {
      type: Array,
    },
  },
  computed: {
    dataColors() {
      if (this.plotColor) {
        return [this.plotColor, this.plotColor];
      } else {
        return constants.colorCycle;
      }
    },
    gains() {
      const modes = this.retrieveByIndiId(`${this.gainCtrlDevice}.modes`);
      const loopState = this.retrieveValueByIndiId(`${this.device}.loop_state.toggle`);
      const loopGain = this.retrieveValueByIndiId(`${this.device}.loop_gain.current`);
      if (!modes || !loopState) {
        return null;
      }
      const totalModes = modes._elements['total']._value;
      const totalBlocks = modes._elements['blocks']._value;
      let gainsData = [];
      // let scaledGainsData = [];
      let startIdx = 0;
      let nModesClosed = 0;
      for (let i = 0; i < totalBlocks; i++) {
        const blockIndex = this.applyFormatString("%02i", i);
        const modesPerBlock = modes._elements[`block${blockIndex}`]._value;
        const blockGain = this.retrieveByIndiId(`${this.gainCtrlDevice}.block${blockIndex}_gain`)?._elements.current._value;
        for (let j = 0; j < modesPerBlock; j++) {
          gainsData.push({ x: startIdx + j, y: blockGain });
          // scaledGainsData.push({ x: startIdx + j, y: loopGain * blockGain });
        }
        startIdx += modesPerBlock;
        if (blockGain > 0) {
          nModesClosed = startIdx;
        }
      }
      return { 
        plotData: {
          gains: { points: gainsData, glowy: true },
          // scaledGains: { points: scaledGainsData, dashed: true },
        },
        nModesClosed 
      };
    },
  },
  mixins: [indi, utils],
  methods: {
  },
  components: {
    PlotComponent,
    FiniteStateMachineStatus,
    LoopState,
    // IndiValue,
    // IndiSwitchMultiElement,
    // IndiSwitchDropdown,
    // IndiToggleSwitch,
    // IndiElement,
    // IndiProperty,
    // IndiCurrentTarget,
    // AlternateIndiToggleSwitch,
    // MaterialIcon,
    // SyncButton
  },
};
</script>