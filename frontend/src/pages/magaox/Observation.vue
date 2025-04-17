<template>
  <div class="observation-controls">
    <observer-control class="padded gap-bottom observer-control"></observer-control>
    <div class="observation-grid" v-if="retrieveValueByIndiId('tcsi.teldata.dome_stat') == 1">
      <telescope-status class="telescope-status" indi-id="tcsi"></telescope-status>
      <danger-zone class="danger-zone padded view"></danger-zone>
    </div>
    <div class="observation-grid">
      <adaptive-optics-loop class="padded view ao-loop holoop" device="holoop" gainCtrlDevice="hogainctrl"
        plotColor="rgb(241, 81, 255)" wfs="camwfs"></adaptive-optics-loop>
      
      <div class="cams-and-corons">
        <table class="status-table view">
          <thead>
            <tr>
              <th></th>
              <th>channel</th>
              <th>camera</th>
              <th>ND</th>
              <th>filter</th>
              <th>exptime/FPS</th>
              <th>gain</th>
              <th>mode</th>
              <th>shutter</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="camName in camNames" :key="camName">
              <td>
                <a v-if="camName != 'visx'" :href="`/video#cam${camName}`" target="_blank">
                  <MaterialIcon name="open_in_new"></MaterialIcon>
                </a>
              </td>
              <td>{{ camName }}</td>
              <td>
                <finite-state-machine-status v-if="retrieveByIndiId(`cam${camName}`)"
                  :indi-id="`cam${camName}`"></finite-state-machine-status>
              </td>
              <td>
                <indi-switch-dropdown v-if="(camName == 'sci1' || camName == 'sci2') && retrieveByIndiId(`fwscind`)"
                  :indi-id="`fwscind.filterName`"></indi-switch-dropdown>
              </td>
              <td v-if="retrieveByIndiId(`fw${camName}`)">
                <indi-switch-dropdown v-if="retrieveByIndiId(`fw${camName}`)"
                  :indi-id="`fw${camName}.filterName`"></indi-switch-dropdown>
              </td>
              <td v-else-if="camName == 'flowfs' && retrieveByIndiId(`fwlowfs`)">
                <indi-switch-dropdown v-if="retrieveByIndiId(`fwlowfs`)"
                  :indi-id="`fwlowfs.filterName`"></indi-switch-dropdown>
              </td>
              <td v-else-if="retrieveByIndiId(`cam${camName}.current_exposure`)">
                <progress :value="100 - retrieveValueByIndiId(`cam${camName}.current_exposure.remaining_pct`)"
                  max="100"></progress>
              </td>
              <td v-else></td>
              <td v-if="retrieveValueByIndiId(`cam${camName}.fps.current`) > 1">
                <indi-current-target :indi-id="`cam${camName}.fps`" format="%1.3f" style="display: inline-block"
                  width="8rem" suffix="FPS"></indi-current-target>
              </td>
              <td v-else-if="retrieveByIndiId(`cam${camName}.exptime`)">
                <indi-current-target :indi-id="`cam${camName}.exptime`" format="%1.3f" style="display: inline-block"
                  width="8rem" suffix="sec"></indi-current-target>
              </td>
              <td v-if="retrieveByIndiId(`cam${camName}.expose.request`)">
                <indi-momentary-switch :indi-id="`cam${camName}.expose.request`"
                  label="begin exposuring"></indi-momentary-switch>
              </td>
              <td v-else-if="retrieveByIndiId(`cam${camName}.emgain`)">
                <indi-current-target :indi-id="`cam${camName}.emgain`"></indi-current-target>
              </td>
              <td v-else></td>
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
      </div>
      <sparkles-control class="view sparkles" indi-id="tweeterSpeck"></sparkles-control>
      <div class="padded view maggie">
        <maggie-o-x></maggie-o-x>
      </div>
      <div class="padded view logs">
        <observer-logs class="logs"></observer-logs>
        <log-stream>
        </log-stream>
      </div>
      <adaptive-optics-loop class="padded view ao-loop loloop" device="loloop" gainCtrlDevice="logainctrl"
        plotColor="#f39c1f" wfs="camflowfs"></adaptive-optics-loop>
    </div>

    <div class="cols top-level">
      <div class="col">

        <div v-for="lightPathGrouping in Object.keys(lightPathDevices)" class="gap-bottom light-path">
          <h2>{{ lightPathGrouping }}</h2>
          <div class="status-tiles">
            <compact-filter-stage-control v-for="deviceName in lightPathDevices[lightPathGrouping]"
              :device-name="deviceName" class="view"></compact-filter-stage-control>
          </div>
        </div>
      </div>
      <div class="col">
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
        <!-- <div class="padded view gap-bottom"> -->
          <!-- <maggie-o-x></maggie-o-x> -->
          <!-- <div>
          purepyindi_example.uptime.uptime_sec: <indi-value indi-id="purepyindi_example.uptime.uptime_sec"></indi-value>
        </div>
        <div>
          Toggle example: <IndiToggleSwitch indi-id="purepyindi_example.obs_on.toggle"></IndiToggleSwitch>
        </div>
        <MaterialIcon name="help"></MaterialIcon> -->
        <!-- </div> -->

      </div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.cams-and-corons {
  // padding: 0.5rem;
  // grid-template-columns: 1fr 3fr 1fr;
  grid-column: 4/13;
}

.ao-loop {
  &.holoop {
    grid-column: 1/4;
  }

  &.loloop {
    grid-column: 1/4;
  }
}

.sparkles {
  grid-column: 1/4;
}

.maggie {
  grid-column: 4/8;
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
    font-variant: small-caps;
  }
}

.observation-controls {
  .observation-grid {
    grid-template-columns: repeat(12, calc(1/12 * 100% - $lggap));
    gap: $lggap;
    padding: $lggap;
    display: grid;

    .telescope-status {
      grid-column: 1/11;
    }

    .danger-zone {
      grid-column: 11/13;
    }

    .telescope-status,
    .danger-zone {
      grid-row: 1/5;
    }
  }

  //   transition: background 1s;
  .observer-control {
    background: $icon-gray;
    padding: $lggap;
  }


  //   &.active {
  //       background: $plasma-blue;
  //       color: var(--fg-normal);
  //   }

  //   .status-tiles {
  //   }
}

.telescope-controls {
  display: grid;
  grid-template-columns: 5fr 12fr;
  grid-gap: $unit;
}

.telescope.cols {
  grid-template-columns: 4fr 1fr;
  align-items: stretch;
}

.logs {
  grid-column: 8/13;
}
</style>
<script>
import utils from "@/mixins/utils.js";
import ObserverControl from "@/components/instrument/ObserverControl.vue";
import CompactFilterStageControl from "@/components/instrument/CompactFilterStageControl.vue";
import ObserverLogs from "@/components/instrument/ObserverLogs.vue";
import ObserverSavingMonitor from "@/components/instrument/ObserverSavingMonitor.vue";
import DangerZone from "@/components/instrument/DangerZone.vue";
import IndiValue from "@/components/indi/IndiValue.vue";
import IndiProperty from "@/components/indi/IndiProperty.vue";
import IndiCurrentTarget from "@/components/indi/IndiCurrentTarget.vue";
import IndiSwitchMultiElementValue from "@/components/indi/IndiSwitchMultiElementValue.vue";
import IndiSwitchMultiElement from "@/components/indi/IndiSwitchMultiElement.vue";
import IndiSwitchDropdown from '@/components/indi/IndiSwitchDropdown.vue';
import IndiToggleSwitch from "@/components/indi/IndiToggleSwitch.vue";
import TelescopeStatus from "@/components/instrument/TelescopeStatus.vue";
import LogStream from "@/components/instrument/LogStream.vue";
import MaterialIcon from '@/components/basic/MaterialIcon.vue';
import FiniteStateMachineStatus from '@/components/instrument/FiniteStateMachineStatus.vue';
import IndiMomentarySwitch from '@/components/indi/IndiMomentarySwitch.vue';
import MaggieOX from "@/components/instrument/MaggieOX.vue";
import SparklesControl from "@/components/instrument/SparklesControl.vue";
import AdaptiveOpticsLoop from "@/components/instrument/AdaptiveOpticsLoop.vue";
import ObservabilityPlots from '@/components/plots/ObservabilityPlots.vue';
export default {
  mixins: [utils],
  inject: ["indi"],
  data: function () {
    return {
      camNames: ["sci1", "sci2", "wfs", "flowfs", "llowfs", "tip", "acq", "visx"],
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
      essentialDevices: ['fwfpm', 'stagescibs', 'fwlyot'],
      lightPathDevices: {
        "entrance-lab": [
          "fwtelsim",
          "stagepickoff",
          "stagebs",
        ],
        "entrance-tel": [
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
          "stagepiaa",
          "fwfpm"
        ],
        "lowfs": [
          "stagelosel",
          "fwlowfs",
          "stageflowfs",
          "stagellowfs",
        ],
        "sci": [
          "fwlyot",
          "stageipiaa",
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
    },
    showCamFpsOrExptime(camName) {
      const exptime = this.retrieveByIndiId(`cam${camName}.exptime.current`);
      const fps = this.retrieveByIndiId(`cam${camName}.fps.current`);
      if (fps && fps._value > 0) {
        return "fps";
      } else if (exptime) {
        return "s";
      } else {
        return "";
      }
    }
  },
  computed: {
    labMode() {
      return this.retrieveValueByIndiId('tcsi.labMode.toggle') == 'On' || !this.retrieveByIndiId('tcsi');
    },
    equatorialCoords() {
      let catData = this.retrieveByIndiId('tcsi.catdata');
      if (catData) {
        return {
          ra: catData._elements.ra._value,
          dec: catData._elements.dec._value,
        };
      }
    }
  },
  components: {
    AdaptiveOpticsLoop,
    ObserverControl,
    ObserverLogs,
    IndiValue,
    IndiCurrentTarget,
    CompactFilterStageControl,
    IndiSwitchMultiElementValue,
    IndiToggleSwitch,
    IndiMomentarySwitch,
    TelescopeStatus,
    MaterialIcon,
    FiniteStateMachineStatus,
    DangerZone,
    IndiSwitchDropdown,
    IndiSwitchMultiElement,
    LogStream,
    ObserverSavingMonitor,
    MaggieOX,
    SparklesControl,
    IndiProperty,
    ObservabilityPlots,
  },
};
</script>