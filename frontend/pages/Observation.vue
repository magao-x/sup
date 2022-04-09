<template>
  <div class="observation-controls cols">
    <div class="col">
      <div class="view flipper warning gap-bottom" v-if="retrieveValueByIndiId('pdu0.source.state') == 'On'">
        <material-icon name="warning"></material-icon> calibration source is on
      </div>
      <div class="view flipper warning gap-bottom" v-if="retrieveValueByIndiId('flipacq.position.in') == 'On'">
        <material-icon name="warning"></material-icon> flipacq is in the beam
      </div>
      <div class="view flipper warning gap-bottom" v-if="retrieveValueByIndiId('flipwfsf.position.in') == 'On'">
        <material-icon name="warning"></material-icon> flipwfsf is in the beam
      </div>
      <observer-control class="observer-control padded gap-bottom"></observer-control>
      <telescope-status indi-id="tcsi" class="padded"></telescope-status>
    </div>
    <div class="col">
      <table class="status-table view gap-bottom">
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
      <div class="status-tiles">
        <div class="status-tile view" v-for="filterWheelName in otherFilterWheels" :key="filterWheelName">
          <div><span class="name">{{ filterWheelName }}</span> <finite-state-machine-status v-if="retrieveByIndiId(filterWheelName)" :indi-id="filterWheelName"></finite-state-machine-status>
          <material-icon name="question_mark" v-else></material-icon></div>
          <indi-switch-multi-element-value
                :indi-id="`${filterWheelName}.filterName`"
              ></indi-switch-multi-element-value>
        </div>
        <div class="status-tile view" v-for="stageName in otherStages" :key="stageName">
          <div><span class="name">{{ stageName }}</span> <finite-state-machine-status v-if="retrieveByIndiId(stageName)" :indi-id="stageName"></finite-state-machine-status>
          <material-icon name="question_mark" v-else></material-icon></div>
          <indi-value
            :indi-id="`${stageName}.position.current`"
          ></indi-value>
          (<indi-switch-multi-element-value
            :indi-id="`${stageName}.presetName`"
          ></indi-switch-multi-element-value>)
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

.gap-bottom { margin-bottom: $unit; }
.observation-controls {
.flipper.warning {
  background: $beware-orange;
  border-color: lighten($beware-orange, 20%);
  font-size: 125%;
  padding: $unit;
}}

.status-tiles {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  grid-template-rows: 1fr;
  gap: $unit;
  align-items: stretch;
  .status-tile {
    margin-bottom: 0;
    text-align: center;
    padding: $medgap;
    .name {
      color: var(--fg-active);
      font-weight: bold;
    }
  }
}

// .observer-control { padding: $unit; }
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