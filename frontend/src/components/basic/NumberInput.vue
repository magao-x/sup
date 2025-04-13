<template>
  <div class="number-input">
      <button v-if="showStep" :disabled="disabled">
      -{{ 10 * step }}
      </button><button v-if="showStep" :disabled="disabled">
      -{{ step }}
      </button><input v-model="userInput"><button v-if="showStep" :disabled="disabled">
      +{{ step }}
      </button><button v-if="showStep" :disabled="disabled">
      +{{ 10 * step }}
      </button>
  </div>
</template>
<style lang="scss" scoped>
@use '@/css/variables.scss' as *;
.number-input { flex: 1; display: flex; }
input {
    flex: 1;
    width: $unit;
    min-width: $unit;
    text-align: center;
}
button, button:hover {
  border-right: none;
  margin-left: 0;
  margin-right: 0;
  border-radius: 0;
}
button:first-child {
  border-radius: $round-radius 0 0 $round-radius;
}
button:last-child {
  border-radius: 0 $round-radius $round-radius 0;
}
</style>
<script>

export default {
  props: ["value", "min", "max", "step", "disabled"],
  data: function () {
    return {"userInput": this.value}
  },
  computed: {
    isValid: function () {
      const numericVal = Number(this.userInput);
      if(!isNaN(numericVal) && numericVal < this.max && numericVal > this.min) {
        return true;
      }
      return false;
    },
    showStep: function () {
      return this.hasStep && !this.disabled;
    },
    hasStep: function () {
      if(this.step != 0) {
        return true;
      }
      return false;
    }
  }
}
</script>
