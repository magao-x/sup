<template>
  <div class="observation-controls cols">
    <div class="padded col">
      <observer-control class="observer-control padded"></observer-control>
      <telescope-status indi-id="tcsi" class="padded"></telescope-status>
    </div>
    <div class="padded col">
      
      <div class="view flipper warning" v-if="retrieveValueByIndiId('flipacq.position.in') == 'On'">
        <material-icon name="warning"></material-icon> flipacq is in the beam
      </div>
      <div class="view flipper warning" v-if="retrieveValueByIndiId('flipwfsf.position.in') == 'On'">
        <material-icon name="warning"></material-icon> flipwfsf is in the beam
      </div>
      <table class="status-table view">
        <thead>
          <tr>
            <th>channel</th>
            <th>camera</th>
            <th>shutter</th>
            <th>writer</th>
            <th>filter</th>
            <th>focus</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="camName in camNames" :key="camName">
            <td>{{ camName }}</td>
            <td>
              <finite-state-machine-status v-if="retrieveByIndiId(`cam${camName}`)" :indi-id="`cam${camName}`" :verbose="true"></finite-state-machine-status>
              <material-icon name="question_mark" v-else></material-icon>
              <!-- <indi-value :indi-id="`cam${camName}.fsm.state`"></indi-value> -->
            </td>
            <td>
              <indi-value
                :indi-id="`cam${camName}.shutter.toggle`"
                on-text="Shut"
                off-text="Open"
              ></indi-value>
            </td>
            <td>
              <indi-value
                :indi-id="`cam${camName}-sw.writing.toggle`"
                on-text="Writing"
                off-text="Paused"
              ></indi-value>
            </td>
            <td>
              <indi-switch-multi-element-value
                :indi-id="`fw${camName}.filterName`"
              ></indi-switch-multi-element-value>
            </td>
            <td>
              <indi-value
                :indi-id="`stage${camName}.position.current`"
              ></indi-value>
              (<indi-switch-multi-element-value
                :indi-id="`stage${camName}.presetName`"
              ></indi-switch-multi-element-value>)
            </td>
          </tr>
        </tbody>
      </table>
      <table class="status-table view">
        <thead>
          <tr>
            <th v-for="filterWheelName in otherFilterWheels" :key="filterWheelName">
              {{ filterWheelName }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td v-for="filterWheelName in otherFilterWheels" :key="filterWheelName">
              <indi-switch-multi-element-value
                :indi-id="`${filterWheelName}.filterName`"
              ></indi-switch-multi-element-value>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="status-tiles">
        <div class="status-tile view" v-for="stageName in otherStages" :key="stageName">
          <div><span class="name">{{ stageName }}</span> <finite-state-machine-status v-if="retrieveByIndiId(stageName)" :indi-id="stageName"></finite-state-machine-status>
          <material-icon name="question_mark" v-else></material-icon></div>
          <indi-switch-multi-element-value
                :indi-id="`${stageName}.presetName`"
              ></indi-switch-multi-element-value>
        </div>
        <div class="status-tile view" v-for="flipName in ['flipacq', 'fliptip', 'flipwfsf']" :key="flipName">
          <div class="name">
            {{flipName}}
            <finite-state-machine-status v-if="retrieveByIndiId(flipName)" :indi-id="flipName"></finite-state-machine-status>
            <material-icon name="question_mark" v-else></material-icon>
          </div>
          <indi-switch-multi-element-value
            :indi-id="`${flipName}.position`"
          ></indi-switch-multi-element-value>
        </div>
      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";
.status-table { width: 100%; text-align: center;
    th {
        color: $hyper-blue;
    }
}
// .status-tiles {
//   display: flex;
//   flex-direction: row;
// }
.observation-controls {
.flipper.warning {
  background: $beware-orange;
  border-color: lighten($beware-orange, 20%);
  font-size: 125%;
}}

.status-tiles {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
  grid-template-rows: 1fr;
  gap: $lggap;
  align-items: stretch;
  .status-tile {
    margin-bottom: 0;
    text-align: center;
    .name {
      color: var(--fg-active);
      font-weight: bold;
    }
  }
}

.observer-control { padding: $unit; }
</style>
<script>
import utils from "~/mixins/utils.js";
import ObserverControl from "~/components/instrument/ObserverControl.vue";
import IndiValue from "../components/indi/IndiValue.vue";
import IndiSwitchMultiElementValue from "../components/indi/IndiSwitchMultiElementValue.vue";
import TelescopeStatus from "../components/instrument/TelescopeStatus.vue";
import MaterialIcon from '../components/basic/MaterialIcon.vue';
import FiniteStateMachineStatus from '../components/instrument/FiniteStateMachineStatus.vue';

export default {
  mixins: [utils],
  data: function () {
    return {
      camNames: ["sci1", "sci2"],
      otherFilterWheels: ["fwlyot", "fwpupil", "fwscind", "fwfpm", "fwlowfs", "fwtelsim"],
      otherStages: ["stageadc1", "stageadc2", "stagebs", "stagecamlensx", "stagecamlensy", "stagek", "stagelosel", "stagelowfs", "stagescibs", "stagepickoff"],
    };
  },
  components: {
    ObserverControl,
    IndiValue,
    IndiSwitchMultiElementValue,
    TelescopeStatus,
    MaterialIcon,
    FiniteStateMachineStatus,
  },
};
</script>