<template>
<div class="warnings">
    <div class="view state-warning" v-for="warning in warnings" :key="warning.message">
        <material-icon name="warning"></material-icon> {{ warning.message }}
    </div>
</div>
</template>
<style lang="scss">
@import '~/css/variables.scss';
.warnings {
    display: flex;
    position: fixed;
    top: 0;
    right: 0;
    z-index: 1000;
    width: 100vw;
}
body:has(.state-warning) {
    padding-top: 6rem;
}
body.dark .view.state-warning {
  background: $beware-orange;
  border: none; //lighten($beware-orange, 20%);
  font-size: 1.75rem;
  padding: $unit;
  flex: 1;
  text-align: center;
  height: 3.7rem;
}
</style>
<script>
import utils from "~/mixins/utils.js";
import indi from "~/mixins/indi.js";
import MaterialIcon from "~/components/basic/MaterialIcon.vue";
export default {
    mixins: [utils, indi],
    components: {
        MaterialIcon
    },
    inject: ["indi"],
    computed: {
        warnings() {
            const labMode = this.retrieveValueByIndiId('stagepickoff.presetName.tel') == 'Off';
            const loopClosed = this.retrieveValueByIndiId('holoop.loop_state.toggle') == 'On';
            const unfilteredWarnings = [
                {
                    message: "calibration source is on",
                    condition: !labMode && this.retrieveValueByIndiId('pdu0.source.state') == 'On'
                },
                {
                    message: "flipacq is in the beam",
                    condition: this.retrieveValueByIndiId('flipacq.presetName.in') == 'On'
                },
                {
                    message: "fwscind is in the beam",
                    condition: !labMode && !(
                        this.retrieveValueByIndiId('fwscind.filterName.open') == 'On' ||
                        this.retrieveValueByIndiId('fwscind.filterName.open2') == 'On'
                    )
                },
                {
                    message: "flipwfsf is in the beam",
                    condition: !labMode && this.retrieveValueByIndiId('flipwfsf.position.in') == 'On'
                },
                {
                    message: "loop closed without tracking and offloading",
                    condition: (
                        loopClosed && !labMode &&
                        !(
                          this.retrieveValueByIndiId('ktrack.tracking.toggle') == 'On' &&
                          this.retrieveValueByIndiId('adctrack.tracking.toggle') == 'On' &&
                          this.retrieveValueByIndiId('tcsi.offlTT_enable.toggle') == 'On'
                        )
                    )
                },
                {
                    message: "loop closed without camwfs alignment loop active",
                    condition: (
                        loopClosed && !labMode &&
                        !(
                          this.retrieveValueByIndiId('camwfs-align.loop_state.toggle') == 'On'
                        )
                    )
                },
                {
                    message: "recording, but camsci1 is not writing",
                    condition: !labMode && (
                        this.retrieveValueByIndiId('observers.obs_on.toggle') == 'On' &&
                        !(this.retrieveValueByIndiId('camsci1-sw.writing.toggle') == 'On')
                    )
                },
                {
                    message: "recording, but camsci2 is not writing",
                    condition: !labMode && (
                        this.retrieveValueByIndiId('observers.obs_on.toggle') == 'On' &&
                        !(this.retrieveValueByIndiId('camsci2-sw.writing.toggle') == 'On') &&
                        !(this.retrieveValueByIndiId('stagescibs.presetName.out') == 'On')
                    )
                },
                {
                    message: "camsci1 is not operating",
                    condition: (
                        this.retrieveValueByIndiId("camsci1.fsm.state") !== "POWEROFF"
                        && 
                        this.retrieveValueByIndiId("camsci1.fsm.state") !== "OPERATING"
                    )
                },
                {
                    message: "camsci2 is not operating",
                    condition: (
                        this.retrieveValueByIndiId("camsci2.fsm.state") !== "POWEROFF"
                        && 
                        this.retrieveValueByIndiId("camsci2.fsm.state") !== "OPERATING"
                    )
                },
                {
                    message: "stagescis are not focused",
                    condition: (
                        (this.retrieveValueByIndiId("stagesci1.presetName.fpm") !== "On") ||
                        (this.retrieveValueByIndiId("stagesci2.presetName.fpm") !== "On")
                    )
                }
            ];
            return unfilteredWarnings.filter((elem) => (elem.condition && this.indi.indiIsConnected));
        }
    }
}
</script>