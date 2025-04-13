<template>
  <div class="status-tile">
    <div>
      <span class="name">{{ deviceName }}</span>
      <finite-state-machine-status v-if="retrieveByIndiId(deviceName)"
        :indi-id="deviceName"></finite-state-machine-status>
      <div v-else>waiting for app</div>
    </div>
    <template v-if="retrieveByIndiId(`${deviceName}`)">
      <indi-switch-dropdown v-if="deviceName.match(/^fw/)" :indi-id="`${deviceName}.filterName`"></indi-switch-dropdown>
      <indi-switch-multi-element v-if="deviceName.match(/^flip/)" :indi-id="`${deviceName}.presetName`"
        :columns="2"></indi-switch-multi-element>
      <template v-if="deviceName.match(/^stage/)">
        <indi-momentary-switch v-if="retrieveValueByIndiId(`${deviceName}.fsm.state`) == 'NOTHOMED'"
          :indi-id="`${deviceName}.home.request`" label="😾"
          style="line-height: 100%; padding:0; vertical-align: middle"></indi-momentary-switch>
        <indi-switch-dropdown v-if="retrieveByIndiId(`${deviceName}`)"
          :indi-id="`${deviceName}.presetName`"></indi-switch-dropdown>
        (<indi-value :indi-id="`${deviceName}.position.current`"></indi-value>)
      </template>
    </template>
  </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;
</style>
<script>
import utils from "@/mixins/utils.js";
import FiniteStateMachineStatus from '@/components/instrument/FiniteStateMachineStatus.vue';
import IndiSwitchDropdown from '@/components/indi/IndiSwitchDropdown.vue';
import IndiSwitchMultiElement from "@/components/indi/IndiSwitchMultiElement.vue";
import IndiValue from "@/components/indi/IndiValue.vue";
export default {
  mixins: [utils],
  props: ["deviceName"],
  components: {
    FiniteStateMachineStatus,
    IndiSwitchDropdown,
    IndiSwitchMultiElement,
    IndiValue,
  }
}
</script>