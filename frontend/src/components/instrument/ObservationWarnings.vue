<template>
    <div class="warnings">
        <div class="warnings-scroll-content" :style="scrollStyle">
            <div class="view state-warning" v-for="warning in warnings" :key="warning.message">
                <material-icon name="warning"></material-icon>
                {{ warning.message }}
            </div>
            <div class="view state-warning" v-for="warning in warnings" :key="warning.message">
                <material-icon name="warning"></material-icon>
                {{ warning.message }}
            </div>
        </div>
    </div>
</template>
<style lang="scss">
@use "@/css/variables.scss" as *;

.warnings {
    background: $beware-orange;
    position: relative;
    /*    width: 100vw;
    overflow-x: scroll;
    overflow-y: hidden;*/
}

.warnings-scroll-content {
    width: 200vw;
    position: relative;
    overflow-x: scroll;
    /*
    overflow-y: hidden;
    scrollbar-width: none; */
    display: flex;
    flex-direction: row;
}

.state-warning {
    width: 100vw;
    font-size: 1.75rem;
    padding: $unit;
    text-align: center;
    box-sizing: border-box;
    color: var(--fg-normal);
}

.dark-mode .view.state-warning {
    background: transparent;
    border: none;
}
</style>
<script>
import utils from "@/mixins/utils.js";
import indi from "@/mixins/indi.js";
import MaterialIcon from "@/components/basic/MaterialIcon.vue";

const millisecondsPerPeriod = 20_000;

export default {
    mixins: [utils, indi],
    components: {
        MaterialIcon,
    },
    inject: ["indi"],
    mounted() {
        this.timer = requestAnimationFrame(this.updateScroll);
    },
    unmounted() {
        cancelAnimationFrame(this.timer);
    },
    methods: {
        updateScroll(dt) {
            if (this.$el) {
                this.totalWidth = this.$el.offsetWidth;
                // range from left: -totalWidth to +totalWidth;
                this.scrollPhase =
                    ((this.scrollPhase + dt) % millisecondsPerPeriod) /
                    millisecondsPerPeriod;
                this.scrollPositionPx =
                    this.scrollPhase * this.totalWidth - this.totalWidth;
            }
            this.timer = requestAnimationFrame(this.updateScroll);
        },
    },
    data() {
        return {
            timer: null,
            totalWidth: 0,
            scrollPhase: 0,
            scrollPositionPx: 0,
        };
    },
    computed: {
        scrollStyle() {
            return {
                left: `${this.scrollPositionPx}px`,
            };
        },
        warnings() {
            const labMode =
                this.retrieveValueByIndiId("tcsi.labMode.toggle") == "On" ||
                this.retrieveValueByIndiId("stagepickoff.presetName.tel") ==
                "Off";
            const loopClosed =
                this.retrieveValueByIndiId("holoop.loop_state.toggle") == "On";
            let coronShortName = null;
            if (
                this.retrieveValueByIndiId("fwfpm.filterName.knifemask") ==
                "On" ||
                this.retrieveValueByIndiId("fwfpm.filterName.knifemaskZ") ==
                "On" ||
                this.retrieveValueByIndiId("fwfpm.filterName.open") == "On"
            ) {
                coronShortName = "knifemask";
            } else if (
                this.retrieveValueByIndiId("fwfpm.filterName.lyotlg") == "On" ||
                this.retrieveValueByIndiId("fwlyot.filterName.LyotLg1") == "On"
            ) {
                coronShortName = "lyotlg";
            } else if (
                this.retrieveValueByIndiId("fwfpm.filterName.lyotsm") == "On" ||
                this.retrieveValueByIndiId("fwlyot.filterName.LyotSm") == "On"
            ) {
                coronShortName = "lyotsm";
            }

            let scibsShortName = null;
            if (
                this.retrieveValueByIndiId("stagescibs.presetName.out") == "On"
            ) {
                scibsShortName = "out";
            } else if (
                this.retrieveValueByIndiId("stagescibs.presetName.ri") == "On"
            ) {
                scibsShortName = "ri";
            } else if (
                this.retrieveValueByIndiId("stagescibs.presetName.pol") == "On"
            ) {
                scibsShortName = "pol";
            }
            const anyPIAA = (
                this.retrieveValueByIndiId("stagepiaa.fsm.state") == "READY" &&
                this.retrieveValueByIndiId("stagepiaa.presetName.out") !== "On"
            ) || (
                    this.retrieveValueByIndiId("stageipiaa.fsm.state") == "READY" &&
                    this.retrieveValueByIndiId("stageipiaa.presetName.out") !== "On"
                );
            const allPIAA = (
                this.retrieveValueByIndiId("fwfpm.filterName.cmc") === "On" ||
                this.retrieveValueByIndiId("fwfpm.filterName.cmc2") === "On"
            );
            const observersElems = this.retrieveByIndiId("observers.writers")?._elements;
            let writableStreams = [];
            if (observersElems) {
                writableStreams = Object.keys(observersElems);
            }
            const isRecording = this.retrieveValueByIndiId("observers.obs_on.toggle") == "On";
            const unfilteredWarnings = [
                {
                    message: "calibration source is on",
                    condition:
                        !labMode &&
                        this.retrieveValueByIndiId("pdu0.source.state") == "On",
                },
                {
                    message: "flipacq is in the beam",
                    condition:
                        this.retrieveValueByIndiId("flipacq.presetName.in") ==
                        "On",
                },
                {
                    message: "fwscind is in the beam",
                    condition:
                        !labMode &&
                        !(
                            this.retrieveValueByIndiId(
                                "fwscind.filterName.open",
                            ) == "On" ||
                            this.retrieveValueByIndiId(
                                "fwscind.filterName.open2",
                            ) == "On"
                        ),
                },
                {
                    message: "flipwfsf is in the beam",
                    condition:
                        !labMode &&
                        this.retrieveValueByIndiId("flipwfsf.position.in") ==
                        "On",
                },
                {
                    message: "loop closed without tracking and offloading",
                    condition:
                        loopClosed &&
                        !labMode &&
                        !(
                            this.retrieveValueByIndiId(
                                "ktrack.tracking.toggle",
                            ) == "On" &&
                            this.retrieveValueByIndiId(
                                "adctrack.tracking.toggle",
                            ) == "On" &&
                            this.retrieveValueByIndiId(
                                "tcsi.offlTT_enable.toggle",
                            ) == "On"
                        ),
                },
                {
                    message: "loop closed without camwfs alignment loop active",
                    condition:
                        loopClosed &&
                        !labMode &&
                        !(
                            this.retrieveValueByIndiId(
                                "camwfs-align.loop_state.toggle",
                            ) == "On"
                        ),
                },
                {
                    message: "recording, but camsci1 is not writing",
                    condition:
                        !labMode &&
                        isRecording &&
                        !(
                            this.retrieveValueByIndiId(
                                "camsci1-sw.writing.toggle",
                            ) == "On"
                        ),
                },
                {
                    message: "recording, but camsci2 is not writing",
                    condition:
                        !labMode &&
                        isRecording &&
                        !(
                            this.retrieveValueByIndiId(
                                "camsci2-sw.writing.toggle",
                            ) == "On"
                        ) &&
                        !(
                            this.retrieveValueByIndiId(
                                "stagescibs.presetName.out",
                            ) == "On"
                        ),
                },
                {
                    message: "camsci1 is not operating",
                    condition:
                        this.retrieveValueByIndiId("camsci1.fsm.state") !==
                        "POWEROFF" &&
                        this.retrieveValueByIndiId("camsci1.fsm.state") !==
                        "OPERATING",
                },
                {
                    message: "camsci2 is not operating",
                    condition:
                        this.retrieveValueByIndiId("camsci2.fsm.state") !==
                        "POWEROFF" &&
                        this.retrieveValueByIndiId("camsci2.fsm.state") !==
                        "OPERATING",
                },
                {
                    message: "PIAA is only partly configured",
                    condition: anyPIAA && !allPIAA,
                },
            ];
            for (let streamName of writableStreams) {
                const thisStreamWriterToggle = this.retrieveValueByIndiId(`${streamName}-sw.writing.toggle`);
                const thisStreamWriterFsm = this.retrieveValueByIndiId(`${streamName}-sw.fsm.state`);

                unfilteredWarnings.push({
                    message: `recording, but ${streamName} not writing`,
                    condition: (
                        isRecording &&
                        observersElems[streamName]?._value == "On" &&
                        (!(thisStreamWriterToggle == "On") ||
                        !(thisStreamWriterFsm == "OPERATING"))
                    ),
                })
            }
            return unfilteredWarnings.filter(
                (elem) => elem.condition && this.indi.indiIsConnected,
            );
        },
    },
};
</script>
