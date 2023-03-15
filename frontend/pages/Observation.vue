<template>
  <div class="observation-controls">
    <observer-saving-monitor class="padded gap-bottom"></observer-saving-monitor>
    
    <div class="cols top-level">
      <div class="col">
        <div class="obs-and-sparkles">
          <observer-control class="observer-controls view padded"></observer-control>
          <sparkles-control indi-id="tweeterSpeck"></sparkles-control>
        </div>
        <table class="status-table view gap-bottom">
          <thead>
            <tr>
              <th>channel</th>
              <th>camera</th>
              <th>ND</th>
              <th>filter</th>
              <th>exptime</th>
              <th>gain</th>
              <th>mode</th>
              <th>shutter</th>
              <th>view</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="camName in camNames" :key="camName">
              <td>{{ camName }}</td>
              <td>
                <finite-state-machine-status v-if="retrieveByIndiId(`cam${camName}`)"
                  :indi-id="`cam${camName}`"></finite-state-machine-status>
              </td>
              <td>
                <indi-switch-dropdown v-if="(camName == 'sci1' || camName == 'sci2') && retrieveByIndiId(`fwscind`)"
                  :indi-id="`fwscind.filterName`"></indi-switch-dropdown>
                </td>
                <td>
                  <indi-switch-dropdown v-if="retrieveByIndiId(`fw${camName}`)"
                  :indi-id="`fw${camName}.filterName`"></indi-switch-dropdown>
                  <progress 
                    v-if="retrieveByIndiId(`cam${camName}.current_exposure`)"
                    :value="100 - retrieveValueByIndiId(`cam${camName}.current_exposure.remaining_pct`)" max="100"></progress>
              </td>
              <td v-if="!retrieveByIndiId(`cam${camName}.exptime`)">
                <indi-value :indi-id="`cam${camName}.fps.current`"
                  ></indi-value> fps
              </td>
              <td v-else>
                <indi-value v-if="retrieveByIndiId(`cam${camName}.exptime`)"
                  :indi-id="`cam${camName}.exptime.current`"></indi-value> s
              </td>
              <td><indi-value v-if="retrieveByIndiId(`cam${camName}.emgain`)" :indi-id="`cam${camName}.emgain.current`"
                ></indi-value>
                  <indi-value v-if="retrieveByIndiId(`cam${camName}.gain`)" :indi-id="`cam${camName}.gain.current`"
                  ></indi-value>
              </td>
              <td>
                <indi-switch-dropdown v-if="retrieveByIndiId(`cam${camName}.readout_speed`)"
                  :indi-id="`cam${camName}.readout_speed`"></indi-switch-dropdown>
              </td>
              <td>
                <indi-toggle-switch v-if="retrieveByIndiId(`cam${camName}.shutter`)"
                  :indi-id="`cam${camName}.shutter.toggle`" label-off="open" label-on="shut"
                  :disabled="!shutterAvailable(camName)" :prompt="true"></indi-toggle-switch>
              </td>
            </tr>
          </tbody>
        </table>
        
        <div v-for="lightPathGrouping in Object.keys(lightPathDevices)" class="gap-bottom light-path">
          <h2>{{ lightPathGrouping }}</h2>
          <div class="status-tiles">
          <div
            v-for="deviceName in lightPathDevices[lightPathGrouping]"
            class="status-tile view"
          >
            <div>
              <span class="name">{{ deviceName }}</span>
              <finite-state-machine-status
                v-if="retrieveByIndiId(deviceName)"
                :indi-id="deviceName"></finite-state-machine-status>
              <div v-else>waiting for app</div>
            </div>
            <template v-if="retrieveByIndiId(`${deviceName}`)">
            <indi-switch-dropdown v-if="deviceName.match(/^fw/)"
              :indi-id="`${deviceName}.filterName`"></indi-switch-dropdown>
            <indi-switch-multi-element
              v-if="deviceName.match(/^flip/)"
              :indi-id="`${deviceName}.position`"
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
        </div>
        </div>

      </div>
    <div class="col">

      <telescope-status v-if="retrieveByIndiId('tcsi')" indi-id="tcsi"></telescope-status>
      <danger-zone class="padded"></danger-zone>
      <div class="status-tiles gap-bottom">
          <div class="status-tile view">
            <div>
              <span class="name">camsci1</span>
              <finite-state-machine-status v-if="retrieveByIndiId('camsci1')"
                indi-id="camsci1"></finite-state-machine-status>
              <div v-else>waiting for app</div>
            </div>
            <indi-value indi-id="camsci1.temp_ccd.current"></indi-value>ºC
          </div>
          <div class="status-tile view">
            <div>
              <span class="name">camsci2</span>
              <finite-state-machine-status v-if="retrieveByIndiId('camsci2')"
                indi-id="camsci2"></finite-state-machine-status>
              <div v-else>waiting for app</div>
            </div>
            <indi-value indi-id="camsci2.temp_ccd.current"></indi-value>ºC
          </div>
          <div class="status-tile view">
            <div>
              <span class="name">rhtweeter</span>
              <finite-state-machine-status v-if="retrieveByIndiId('rhtweeter')"
                indi-id="rhtweeter"></finite-state-machine-status>
              <div v-else>waiting for app</div>
            </div>
            <indi-value :indi-id="`rhtweeter.humidity.current`"></indi-value>% @ <indi-value
              :indi-id="`rhtweeter.temperature.current`"></indi-value>ºC
          </div>
          <div class="status-tile view">
            <div>
              <span class="name">temprack</span>
              <finite-state-machine-status v-if="retrieveByIndiId('temprack')"
                indi-id="temprack"></finite-state-machine-status>
              <div v-else>waiting for app</div>
            </div>
            <indi-value :indi-id="`temprack.temperature.lower`"></indi-value>ºC L
            / <indi-value :indi-id="`temprack.temperature.upper`"></indi-value>ºC U
          </div>
        </div>
      <div class="padded view gap-bottom">
        <maggie-o-x></maggie-o-x>
        <!-- <div>
          purepyindi_example.uptime.uptime_sec: <indi-value indi-id="purepyindi_example.uptime.uptime_sec"></indi-value>
        </div>
        <div>
          Toggle example: <IndiToggleSwitch indi-id="purepyindi_example.obs_on.toggle"></IndiToggleSwitch>
        </div>
        <MaterialIcon name="help"></MaterialIcon> -->
      </div>
      <div class="padded view">
        <log-stream>
        </log-stream>
      </div>
    </div>
  </div>
</div></template>
<style lang="scss" scoped>
@import "./css/variables.scss";

.cols.top-level {
  grid-template-columns: 1fr 1fr;
}

.status-table {
  width: 100%;
  text-align: center;

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

.light-path {
  h2 {
    font-size: 0.8rem;
    font-variant:small-caps;
  }
}

.obs-and-sparkles {
  display: grid;
  gap: 1rem;
}

.observation-controls {
  .status-tiles {
    grid-template-columns: 1fr 1fr 1fr 1fr;
  }
}

.telescope-controls {
  display: grid;
  grid-template-columns: 5fr 12fr;
  grid-gap: $unit;
}

</style>
<script>
import utils from "~/mixins/utils.js";
import ObserverControl from "~/components/instrument/ObserverControl.vue";
import ObserverSavingMonitor from "~/components/instrument/ObserverSavingMonitor.vue";
import DangerZone from "~/components/instrument/DangerZone.vue";
import IndiValue from "~/components/indi/IndiValue.vue";
import IndiProperty from "~/components/indi/IndiProperty.vue";
import IndiSwitchMultiElementValue from "../components/indi/IndiSwitchMultiElementValue.vue";
import IndiSwitchMultiElement from "../components/indi/IndiSwitchMultiElement.vue";
import IndiSwitchDropdown from '~/components/indi/IndiSwitchDropdown.vue';
import IndiToggleSwitch from "~/components/indi/IndiToggleSwitch.vue";
import TelescopeStatus from "../components/instrument/TelescopeStatus.vue";
import LogStream from "~/components/instrument/LogStream.vue";
import MaterialIcon from '../components/basic/MaterialIcon.vue';
import FiniteStateMachineStatus from '../components/instrument/FiniteStateMachineStatus.vue';
import IndiMomentarySwitch from '../components/indi/IndiMomentarySwitch.vue';
import MaggieOX from "../components/instrument/MaggieOX.vue";
import SparklesControl from "~/components/instrument/SparklesControl.vue";

export default {
  mixins: [utils],
  inject: ["indi"],
  data: function () {
    return {
      camNames: ["sci1", "sci2", "wfs", "lowfs", "tip", "acq", "visx"],
      otherFilterWheels: ["fwlyot", "fwpupil", "fwscind", "fwfpm", "fwlowfs", "fwtelsim"],
      otherStages: [
        "stagescibs", "stagepickoff", "stagebs",
        "stageadc1", "stageadc2",
        "stagecamlensx", "stagecamlensy", "stagek",
        "stagelosel", "stagelowfs",
        "stageturbsim",
        "stagepiaa1", "stagepiaa2",
        "stagesci1", "stagesci2",
      ],
      flipNames: ['fliptip', 'flipwfsf'],
      lightPathDevices: {
        "entrance": [
          "fwtelsim",
          "stagepickoff",
          "stagek",
          "flipacq",
          "stageadc1",
          "stageadc2",
          "stagebs",
        ],
        "wfs": [
          "flipwfsf",
          "fliptip",
          "stagecamlensx",
          "stagecamlensy",
        ],
        "upstream": [
          "fwpupil",
          "stagepiaa1",
          "fwfpm"
        ],
        "lowfs": [
          "stagelosel",
          "fwlowfs",
          "stagelowfs",
        ],
        "sci": [
          "fwlyot",
          "stagepiaa2",
          "fwscind",
          "stagescibs",
          "fwsci1",
          "stagesci1",
          "fwsci2",
          "stagesci2",
        ]
      }
    };
  },
  methods: {
    shutterAvailable(camName) {
      const retval = this.indi.indiIsConnected && this.retrieveByIndiId(`cam${camName}.shutter_status.status`) && (
        this.retrieveByIndiId(`cam${camName}.shutter_status.status`)._value == "READY"
      );
      return retval;
    }
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
    LogStream,
    ObserverSavingMonitor,
    MaggieOX,
    SparklesControl,
    IndiProperty,
  },
};
</script>