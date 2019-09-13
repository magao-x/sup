<template>
  <div>
    <div class="current">
      Current:
      <span v-for="elem in property.elements" :key="elem.name">
        <input
          :type="switchType"
          :name="'current__' + propertyId + '.' + elem.name"
          :checked="elem.value == 'On' ? 'checked' : ''"
          @click.prevent
        />
        <span>{{ elem.name }}</span>
      </span>
    </div>
    <div class="target">
      Target:
      <span v-for="elem in property.elements" :key="elem.name">
        <input
          :type="switchType"
          :name="propertyId"
          :id="propertyId + '.' + elem.name"
          :value="elem.name"
          :disabled="property.state == 'Busy' ? 'disabled' : false"
          v-model="selectedSwitches"
          @change="sendSwitches(elem.name)"
        />
        <label :for="propertyId + '.' + elem.name">{{ elem.name }}</label>
      </span>
    </div>
  </div>
</template>
<style scoped>
</style>
<script>
export default {
  methods: {
      sendSwitches: function (elemName) {
        this.$socket.emit('indi_new', {
            'device': this.device.name,
            'property': this.property.name,
            'element': elemName,
            'value': 'On'
        });
        console.log("sent indi_new")
      }
  },
  data: function() {
    const enabledSwitches = Object.keys(this.property.elements).filter(
      key => this.property.elements[key].value == "On"
    );
    return {
      selectedSwitches:
        this.switchType == "checkbox" ? enabledSwitches : enabledSwitches[0]
    };
  },
  computed: {
    switchType: function() {
      if (this.property.rule == "OneOfMany") {
        return "radio";
      } else {
        return "checkbox";
      }
    },
    propertyId: function () {
      return this.device.name + '.' + this.property.name;
    }
  },
  props: ["device", "property"]
};
</script>
