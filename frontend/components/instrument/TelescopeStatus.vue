<template>
    <div class="view" v-if="indiDefined">
        TCS:
        <div class="cols">
            <div class="col"><div>Catalog</div>
                <div>RA: <indi-value :indi-id="`${thisDevice.name}.catdata.ra`"></indi-value></div>
                <div>Dec: <indi-value :indi-id="`${thisDevice.name}.catdata.dec`"></indi-value></div>
                <div>Epoch: <indi-value :indi-id="`${thisDevice.name}.catdata.epoch`"></indi-value></div>
                <div>Object: <indi-value :indi-id="`${thisDevice.name}.catalog.object`"></indi-value></div>
            </div>
        <div class="col"><div>Current</div>
                <div>RA: <indi-value :indi-id="`${thisDevice.name}.telpos.ra`"></indi-value></div>
                <div>Dec: <indi-value :indi-id="`${thisDevice.name}.telpos.dec`"></indi-value></div>
                <div>Epoch: <indi-value :indi-id="`${thisDevice.name}.telpos.epoch`"></indi-value></div>
        </div>
    </div>
</template>
<script>
import indi from "~/mixins/indi.js";
import utils from "~/mixins/utils.js";
import IndiValue from '../indi/IndiValue.vue';

export default {
    props: ["device", "indiId"],
    mixins: [indi, utils],
    components: {
        IndiValue
        
    }
}
</script>