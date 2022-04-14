<template>
<div>
    <div class="view warning gap-bottom" v-for="warning in warnings" :key="warning.message">
        <material-icon name="warning"></material-icon> {{ warning.message }}
    </div>
</div>
</template>
<style lang="scss" scoped>
@import '~/css/variables.scss';
body.dark .view.warning {
  background: $beware-orange;
  border-color: lighten($beware-orange, 20%);
  font-size: 125%;
  padding: $unit;
}
</style>
<script>
import utils from "~/mixins/utils.js";
import MaterialIcon from "~/components/basic/MaterialIcon.vue";
export default {
    mixins: [utils],
    components: {
        MaterialIcon
    },
    computed: {
        warnings() {
            const unfilteredWarnings = [
                {
                    message: "calibration source is on",
                    condition: this.retrieveValueByIndiId('pdu0.source.state') == 'On'
                },
                {
                    message: "flipacq is in the beam",
                    condition: this.retrieveValueByIndiId('flipacq.position.in') == 'On'
                },
                {
                    message: "flipwfsf is in the beam",
                    condition: this.retrieveValueByIndiId('flipwfsf.position.in') == 'On'
                },
                {
                    message: "loop closed without tracking and offloading",
                    condition: (
                        this.retrieveValueByIndiId('holoop.loop_state.toggle') == 'On' &&
                        !(
                          this.retrieveValueByIndiId('ktrack.tracking.toggle') == 'On' &&
                          this.retrieveValueByIndiId('adctrack.tracking.toggle') == 'On' &&
                          this.retrieveValueByIndiId('tcsi.offlTT_enable.toggle') == 'On'
                        )
                    )
                },
                {
                    message: "recording, but camsci1 is not writing",
                    condition: (
                        this.retrieveValueByIndiId('observers.obs_on.toggle') == 'On' &&
                        !(this.retrieveValueByIndiId('camsci1-sw.writing.toggle') == 'On')
                    )
                },
                {
                    message: "recording, but camsci2 is not writing",
                    condition: (
                        this.retrieveValueByIndiId('observers.obs_on.toggle') == 'On' &&
                        !(this.retrieveValueByIndiId('camsci2-sw.writing.toggle') == 'On')
                    )
                },
            ];
            return unfilteredWarnings.filter((elem) => elem.condition);
        }
    }
}
</script>