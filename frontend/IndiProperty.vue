<template>
    <div class="property">
        <div class="name" :class="{'idle': property.state == 'Idle', 'ok': property.state == 'Ok', 'busy': property.state == 'Busy', 'alert': property.state == 'Alert'}">{{ device.name }}.{{ property.name }}</div>
        <p v-if="property.message !== null">{{ property.message }}</p>
        <template v-if="property.kind == 'swt'">
            <indi-switch-multi-element :device="device" :property="property" />
        </template><template v-else>
            {{ isPairedCurrentTarget }}
            <indi-element v-for="elem in objectAsSortedArray(property.elements)" :key="elem.name" :device="device" :property="property" :element="elem" />
        </template>
    </div>
</template>
<style lang="scss" scoped>
@import './css/variables.scss';

.alert {
  color: $orange;
  border-color: darken($orange, 15);
}
.ok {
  color: $green;
  border-color: darken($green, 15);
}
.busy {
  color: $base2;
}
.idle {
    color: $base1;
}
</style>
<script>
import IndiElement from "./IndiElement.vue";
import IndiLight from "./IndiLight.vue";
import IndiSwitchMultiElement from "./IndiSwitchMultiElement.vue";
import utils from "./utils.js";

export default {
    components: {
        IndiElement,
        IndiSwitchMultiElement,
        IndiLight
    },
    props: ["device", "property"],
    mixins: [utils],
    computed: {
        isPairedCurrentTarget: function () {
            if (this.property.elements.target !== undefined && this.property.elements.current !== undefined) {
                return true;
            }
            return false;
        }
    }
}
</script>
