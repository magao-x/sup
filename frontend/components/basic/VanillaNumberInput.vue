<template>
  <input type="number" :value="value" @input="convertAndEmit($event.target.value)" />
</template>
<script>
export default {
  props: ["value"],
  methods: {
    convertAndEmit(value) {
      const number = Number(value);
      if (value !== null && number !== NaN) {
        this.$emit("input", number);
      }
    }
  }
};
</script>