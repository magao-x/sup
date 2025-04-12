<template>
  <div class="clicky-stepper">
    <button @click="step(-1 * increment)">
      {{ minusLabel }}
    </button>
    <button @click="advanceIncrement">{{ increment }}</button>
    <button @click="step(increment)">
      {{ plusLabel }}
    </button>
  </div>
</template>
<style lang="scss" scoped>
button { min-width: 3em;}
.clicky-stepper {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
}
</style>
<script>
export default {
  data() {
    return { increment: this.increments[0], index: 0 };
  },
  props: {
    increments: {
      type: Array,
      default: () => [5, 1, 0.5],
    },
    label: {
      type: String,
      default: "",
    },
    callback: {
      type: Function,
      default: (amount) => console.log(label, amount)
    },
  },
  computed: {
    plusLabel() { return `+${this.label}`; },
    minusLabel() { return `-${this.label}`; }
  },
  methods: {
    step(amount) {
      this.$emit("step", {label: this.label, amount: amount})
    },
    advanceIncrement() {
      this.index += 1;
      if (this.index >= this.increments.length) {
        this.index = 0;
      }
      this.increment = this.increments[this.index];
    }
  }
}
</script>