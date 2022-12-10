<template>
<!--     v-for="record in filteredFlattenedDevices"
    :key="record.device.name + '.' + record.property.name + '.' + record.element.name" -->
  <tr :class="record.property.state">
    <td>
      <indi-state-indicator :state="record.property.state"></indi-state-indicator>
    </td>
    <td>{{ record.device.name }}</td>
    <td>{{ record.property.name }}</td>
    <td class="kind">{{ record.property.kind }}</td>
    <td>{{ record.element.name }}</td>
    <td
      v-if="record.property.kind == 'num'"
      class="value"
    >{{ applyFormatString(record.element.format, record.element._value) }}</td>
    <td v-else-if="record.property.name == 'fsm'" class="value">
      <finite-state-machine-status :device="record.device"></finite-state-machine-status>
    </td>
    <td v-else class="value">{{ record.element._value }}</td>
    <td class="controls">
      <indi-element :device="record.device" :property="record.property" :element="record.element"></indi-element>
    </td>
  </tr>
</template>
<style lang="scss" scoped>
</style>
<script>
import IndiElement from "~/components/indi/IndiElement.vue";
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";
import IndiStateIndicator from "~/components/indi/IndiStateIndicator.vue";
import utils from "~/mixins/utils.js";

export default {
  props: ["record"],
  mixins: [utils],
  components: {
    IndiElement,
    FiniteStateMachineStatus,
    IndiStateIndicator,
  }
};
</script>