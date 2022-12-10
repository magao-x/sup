<template>
  <div class="observation-controls cols">
    <div class="col">
      <observer-control class="observer-control padded gap-bottom"></observer-control>
      <telescope-status v-if="retrieveByIndiId('tcsi')" indi-id="tcsi"></telescope-status>
      <danger-zone class="padded"></danger-zone>
      <div class="padded view">
        <div>
          purepyindi_example.uptime.uptime_sec: <indi-value indi-id="purepyindi_example.uptime.uptime_sec"></indi-value>
        </div>
        <div>
          Toggle example: <IndiToggleSwitch indi-id="purepyindi_example.obs_on.toggle"></IndiToggleSwitch>
        </div>
      </div>
    </div>
    <div class="col">
      <div class="status-tiles gap-bottom">
        <div class="status-tile view">
          <div>
            <span class="name">camsci1</span>
            <finite-state-machine-status v-if="retrieveByIndiId('camsci1')" indi-id="camsci1"></finite-state-machine-status>
            <div v-else>waiting for app</div>
          </div>
          <indi-value
            indi-id="camsci1.temp_ccd.current"
          ></indi-value>ºC
        </div>
        <div class="status-tile view">
          <div>
            <span class="name">camsci2</span>
            <finite-state-machine-status v-if="retrieveByIndiId('camsci2')" indi-id="camsci2"></finite-state-machine-status>
            <div v-else>waiting for app</div>
          </div>
          <indi-value
            indi-id="camsci2.temp_ccd.current"
          ></indi-value>ºC
        </div>
        <div class="status-tile view">
          <div>
            <span class="name">rhtweeter</span>
            <finite-state-machine-status v-if="retrieveByIndiId('rhtweeter')" indi-id="rhtweeter"></finite-state-machine-status>
            <div v-else>waiting for app</div>
          </div>
          <indi-value
            :indi-id="`rhtweeter.humidity.current`"
          ></indi-value>% @ <indi-value
            :indi-id="`rhtweeter.temperature.current`"
          ></indi-value>ºC
        </div>
        <div class="status-tile view">
          <div>
            <span class="name">temprack</span>
            <finite-state-machine-status v-if="retrieveByIndiId('temprack')" indi-id="temprack"></finite-state-machine-status>
            <div v-else>waiting for app</div>
          </div>
          <indi-value
            :indi-id="`temprack.temperature.lower`"
          ></indi-value>ºC L
          / <indi-value
            :indi-id="`temprack.temperature.upper`"
          ></indi-value>ºC U
        </div>
      </div>
      <table class="status-table view gap-bottom">
        <thead>
          <tr>
            <th>channel</th>
            <th>camera</th>
            <th>exptime</th>
            <th>filter</th>
            <th>mode</th>
            <th>emgain</th>
            <th>shutter</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="camName in camNames" :key="camName">
            <td>{{ camName }}</td>
            <td>
              <finite-state-machine-status v-if="retrieveByIndiId(`cam${camName}`)" :indi-id="`cam${camName}`"></finite-state-machine-status>
            </td>
            <td v-if="!retrieveByIndiId(`cam${camName}.exptime`)">
              <indi-value
                :indi-id="`cam${camName}.fps.current`"
                :formatFunction="(v) => String(Number(v).toFixed(0))"
              ></indi-value> fps
            </td>
            <td v-else>
              <indi-value
                v-if="retrieveByIndiId(`cam${camName}.exptime`)"
                :indi-id="`cam${camName}.exptime.current`"
              ></indi-value> s
            </td>
            <td>
              <indi-switch-dropdown v-if="retrieveByIndiId(`fw${camName}`)" :indi-id="`fw${camName}.filterName`"></indi-switch-dropdown>
            </td>
            <td>
              <indi-switch-dropdown v-if="retrieveByIndiId(`cam${camName}.readout_speed`)" :indi-id="`cam${camName}.readout_speed`"></indi-switch-dropdown>
            </td>
            <td><indi-value
                v-if="retrieveByIndiId(`cam${camName}.emgain`)"
                :indi-id="`cam${camName}.emgain.current`"
                :formatFunction="(v) => String(Number(v).toFixed(0))"
              ></indi-value>
            </td>
            <td>
              <indi-toggle-switch
                v-if="retrieveByIndiId(`cam${camName}.shutter`)"
                :indi-id="`cam${camName}.shutter.toggle`" label-off="open" label-on="shut" :prompt="true"></indi-toggle-switch>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="status-tiles">
        <div class="status-tile view" v-for="filterWheelName in otherFilterWheels" :key="filterWheelName">
          <div>
            <span class="name">{{ filterWheelName }}</span>
            <finite-state-machine-status v-if="retrieveByIndiId(filterWheelName)" :indi-id="filterWheelName"></finite-state-machine-status>
            <div v-else>waiting for app</div>
          </div>
          <indi-switch-dropdown v-if="retrieveByIndiId(`${filterWheelName}`)" :indi-id="`${filterWheelName}.filterName`"></indi-switch-dropdown>
          <!-- <indi-switch-multi-element-value
                :indi-id="`${filterWheelName}.filterName`"
              ></indi-switch-multi-element-value> -->
        </div>
        <div class="status-tile view" v-for="stageName in otherStages" :key="stageName">
          <div>
            <span class="name">{{ stageName }}</span> <finite-state-machine-status v-if="retrieveByIndiId(stageName)" :indi-id="stageName"></finite-state-machine-status>
            <div v-else>waiting for app</div>
          </div>
          <indi-momentary-switch
              v-if="retrieveValueByIndiId(`${stageName}.fsm.state`) == 'NOTHOMED'"
              :indi-id="`${stageName}.home.request`"
              label="😾"
              style="line-height: 100%; padding:0; vertical-align: middle"
          ></indi-momentary-switch>
          <indi-switch-dropdown v-if="retrieveByIndiId(`${stageName}`)" :indi-id="`${stageName}.presetName`"></indi-switch-dropdown>
          (<indi-value
            :indi-id="`${stageName}.position.current`"
          ></indi-value>)
        </div>
        <div class="status-tile view" v-for="flipName in flipNames" :key="flipName">
          <div class="name">
            {{flipName}}
            <finite-state-machine-status v-if="retrieveByIndiId(flipName)" :indi-id="flipName"></finite-state-machine-status>
            <div v-else>waiting for app</div>
          </div>
          <indi-switch-multi-element
            :indi-id="`${flipName}.position`"
            :columns="2"
          ></indi-switch-multi-element>
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
    select {
      width: 100%;
      max-width: 10em;
      padding: $medgap;
      text-align: center;
    }
}
// .status-tiles {
//   display: flex;
//   flex-direction: row;
// }
.observation-controls {
  grid-template-columns: 1fr 1fr;
}

.telescope-controls {
  display: grid;
  grid-template-columns: 5fr 12fr;
  grid-gap: $unit;
}

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
</style>
<script>
import utils from "~/mixins/utils.js";
import ObserverControl from "~/components/instrument/ObserverControl.vue";
import DangerZone from "~/components/instrument/DangerZone.vue";
import IndiValue from "../components/indi/IndiValue.vue";
import IndiSwitchMultiElementValue from "../components/indi/IndiSwitchMultiElementValue.vue";
import IndiSwitchMultiElement from "../components/indi/IndiSwitchMultiElement.vue";
import IndiSwitchDropdown from '~/components/indi/IndiSwitchDropdown.vue';
import IndiToggleSwitch from "~/components/indi/IndiToggleSwitch.vue";
import TelescopeStatus from "../components/instrument/TelescopeStatus.vue";
import MaterialIcon from '../components/basic/MaterialIcon.vue';
import FiniteStateMachineStatus from '../components/instrument/FiniteStateMachineStatus.vue';
import IndiMomentarySwitch from '../components/indi/IndiMomentarySwitch.vue';

export default {
  mixins: [utils],
  inject: ["indi"],
  data: function () {
    return {
      camNames: ["sci1", "sci2", "wfs", "lowfs", "tip", "acq"],
      otherFilterWheels: ["fwlyot", "fwpupil", "fwscind", "fwfpm", "fwlowfs", "fwtelsim"],
      otherStages: [
        "stagescibs", "stagepickoff", "stagebs", 
        "stageadc1", "stageadc2", 
        "stagecamlensx", "stagecamlensy", "stagek", 
        "stagelosel", "stagelowfs",
      ],
      flipNames: ['flipacq', 'fliptip', 'flipwfsf'],
    };
  },

  components: {
    ObserverControl,
    IndiValue,
    IndiSwitchMultiElementValue,
    IndiToggleSwitch,
    TelescopeStatus,
    MaterialIcon,
    FiniteStateMachineStatus,
    DangerZone,
    IndiSwitchDropdown,
    IndiMomentarySwitch,
    IndiSwitchMultiElement,
  },
};
</script>