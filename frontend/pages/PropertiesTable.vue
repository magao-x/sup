<template>
  <div class="indi-properties-table">
    <div class="search-control">
      <span class="search-icon">
        <i class="material-icons">search</i>
      </span>
      <input v-model="searchString" />
      <button class="square" @click="clearFilter" :disabled="!doFilter">
        <i class="material-icons">clear</i>
      </button>
    </div>
    <table>
      <thead>
        <tr>
          <th>state</th>
          <th>device</th>
          <th>property</th>
          <th class="kind">kind</th>
          <th>element</th>
          <th class="value">value</th>
          <th class="controls">control</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="record in filteredFlattenedDevices"
          :key="record.device.name + '.' + record.property.name + '.' + record.element.name"
          :class="record.property.state"
        >
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
          >{{ applyFormatString(record.element.format, record.element.value) }}</td>
          <td
            v-else-if="record.property.name == 'fsm'"
            class="value"
          ><finite-state-machine-status :device="record.device"></finite-state-machine-status></td>
          <td v-else class="value">{{ record.element.value }}</td>
          <td class="controls">
            <indi-element
              :device="record.device"
              :property="record.property"
              :element="record.element"
            ></indi-element>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
.indi-properties-table {
  width: 100%;
}
.search-control {
  position: relative;
  display: flex;
  .search-icon {
    position: absolute;
    left: 0.5 * $unit;
    width: $unit;
    top: 0.25 * $unit;
    box-sizing: border-box;
  }
  input {
    padding-left: 2 * $unit;
    flex: 1;
  }
}

table {
  border-collapse: collapse;
  width: 100%;

  text-align: center;
  tbody > tr:nth-child(odd) {
    background: $base02;
  }
  tbody > tr:hover {
    background: lighten($base02, 5);
  }
  td,
  th {
    // width: 14.2%;
    box-sizing: border-box;
    padding: 0 $unit;
  }
  .kind {
    width: 8%;
  }
  .value {
    width: 124px;
  }
  td.controls {
    text-align: left;
    // padding-left: $unit;
    max-width: 20em;
  }
}
</style>
<script>
import IndiElement from "~/components/indi/IndiElement.vue";
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";
import IndiStateIndicator from "~/components/indi/IndiStateIndicator.vue";
import utils from "~/mixins/utils.js";

export default {
  components: {
    IndiElement,
    IndiStateIndicator,
    FiniteStateMachineStatus
  },
  mixins: [utils],
  computed: {
    doFilter: function () {
      return this.searchString.length > 2;
    },
    filteredFlattenedDevices: function() {
      const devs = [];
      let sstr = this.searchString;
      for (let device of this.objectAsSortedArray(this.$store.state.devices)) {
        for (let property of this.objectAsSortedArray(device.properties)) {
          for (let element of this.objectAsSortedArray(property.elements)) {
            const indiId = `${device.name}.${property.name}.${element.name}`;
            if (!this.doFilter || indiId.includes(sstr)) {
              devs.push({
                device,
                property,
                element
              });
            }
          }
        }
      }
      return devs;
    }
  },
  methods: {
    clearFilter() {
      this.searchString = "";
    }
  },
  data: function() {
    return { searchString: "" };
  }
};
</script>
