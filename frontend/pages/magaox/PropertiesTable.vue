<template>
  <div class="indi-properties-table">
    <div class="row search-control">
      <span class="search-icon">
        <i class="material-icons">search</i>
      </span>
      <input v-model="searchString" />
      <button class="square" @click="clearFilter" :disabled="!doFilter">
        <i class="material-icons">clear</i>
      </button>
    </div>
    <div class="row">
      <div>state</div>
      <div>device</div>
      <div>property</div>
      <div class="kind">kind</div>
      <div>element</div>
      <div class="value">value</div>
      <div class="controls">control</div>
    </div>
    <DynamicScroller :items="filteredFlattenedDevices" :min-item-size="36" class="scroller">
      <template v-slot="{ item, index, active }">
        <DynamicScrollerItem
          :item="item"
          :active="active"
          :size-dependencies="[
                item.message,
              ]"
          :data-index="index"
        >
          <table-row class="element" :record="item"></table-row>
        </DynamicScrollerItem>
      </template>
    </DynamicScroller>
  </div>
</template>
<style lang="scss" scoped>
@use "./css/variables.scss" as *;
.indi-properties-table {
  width: 100%;
  .row {
    .element:nth-child(odd) {
      background: var(--bg-alternate);
    }
    .element:hover {
      background: $abyss-blue;
    }
  }
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
.scroller {
  height: 80vh;
  overflow-y: auto;
}
</style>
<script>
import IndiElement from "~/components/indi/IndiElement.vue";
import FiniteStateMachineStatus from "~/components/instrument/FiniteStateMachineStatus.vue";
import IndiStateIndicator from "~/components/indi/IndiStateIndicator.vue";
import TableRow from "~/pages/properties/TableRow.vue";
import utils from "~/mixins/utils.js";

export default {
  components: {
    IndiElement,
    IndiStateIndicator,
    FiniteStateMachineStatus,
    TableRow
  },
  mixins: [utils],
  computed: {
    doFilter: function() {
      return this.searchString.length > 2;
    },
    filteredFlattenedDevices: function() {
      const devs = [];
      let sstr = this.searchString;
      for (let device of this.objectAsSortedArray(this.indi.world.devices)) {
        for (let property of this.objectAsSortedArray(device)) {
          for (let element of this.objectAsSortedArray(property._elements)) {
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
