<template>
<div class="warnings">
    <div class="view warning" v-for="warning in warnings" :key="warning.message">
        <material-icon name="warning"></material-icon> {{ warning.message }}
    </div>
</div>
</template>
<style lang="scss" scoped>
@import '~/css/variables.scss';
.warnings {
    display: flex;
}
body.dark .view.warning {
  background: $beware-orange;
  border: none; //lighten($beware-orange, 20%);
  font-size: 125%;
  padding: $unit;
  flex: 1;
  text-align: center;
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
    computed: {
        warnings() {
            const labMode = this.retrieveValueByIndiId('stagepickoff.presetName.out') == 'Off';
            const loopClosed = this.retrieveValueByIndiId('holoop.loop_state.toggle') == 'On';
            const unfilteredWarnings = [
                {
                    message: "calibration source is on",
                    condition: !labMode && this.retrieveValueByIndiId('pdu0.source.state') == 'On'
                },
                {
                    message: "flipacq is in the beam",
                    condition: this.retrieveValueByIndiId('flipacq.position.in') == 'On'
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
                        !(this.retrieveValueByIndiId('camsci2-sw.writing.toggle') == 'On')
                    )
                },
            ];
            return unfilteredWarnings.filter((elem) => (elem.condition && this.indiIsConnected));
        }
    }
}
</script>