<template>
  <div>
    <button>
      {{ plusLabel }}
    </button>
    <button @click="advanceIncrement">{{ increment }}</button>
    <button>
      {{ minusLabel }}
    </button>
  </div>
</template>
<style lang="scss" scoped>
button { min-width: 3em;}
</style>
<script>
export default {
  data() {
    return { increment: this.increments[0], index: 0 };
  },
  props: {
    increments: {
      type: Array,
      default: () => [0.5, 1, 5],
    },
    plusLabel: {
      type: String,
      default: "+",
    },
    plusCallback: {
      type: Function,
      default: () => console.log("+!")
    },
    minusLabel: {
      type: String,
      default: "-",
    },
    minusCallback: {
      type: Function,
      default: () => console.log("-!")
    },
  },
  methods: {
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