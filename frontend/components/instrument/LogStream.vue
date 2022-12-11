<template>
  <div>
    <div class="levels">
      <div class="oneLevel" v-for="l in levels">
        <input :id="l" v-model="showLevels" :value="l" type="checkbox"><label :for="l">{{ l }}</label>
      </div>
    </div>
    <div class="short" v-if="mungedLogs.length > 0">
      <table>
        <tbody>
          <tr v-for="log in mungedLogs">
            <td class="timestamp">{{ log.timestamp }}</td>
            <td class="level" :class="log.icon"><material-icon :name="log.icon"></material-icon>&nbsp;{{ log.level }}</td>
            <td class="device">{{ log.device }}</td>
            <td>{{ log.message }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="noLogs" v-else>
      no logs matching these filters
    </div>
  </div>
</template>
<style lang="scss" scoped>
@import "~/css/variables.scss";

.levels {
  display: flex;
  width: 100%;

  .oneLevel {
    flex: 1;

    label {
      padding: 0 1em;
    }
  }
}

.noLogs {
  text-align: center;
  color: $icon-gray;
  padding: 0.5em 0 0 0;
}

.short {
  max-height: 20em;
  overflow-y: scroll;
}

table {
  width: 100%;
}

tbody {
  font-family: monospace;
  font-size: 12px;
}

.timestamp {
  width: 12em;
}

.level {
  width: 5em;
}

.info {
  color: $ok;
}

.error {
  color: $error;
}

.warning {
  color: $warning;
}

.device {
  color: $alternate-gray;
}
</style>
<script>
import utils from "~/mixins/utils.js";
import MaterialIcon from "~/components/basic/MaterialIcon.vue";

const iconLookup = {
  EMER: "error",
  ALRT: "error",
  CRIT: "error",
  ERR: "error",
  WARN: "warning",
  NOTE: "info",
  INFO: "info",
};

export default {
  props: [],
  mixins: [utils],
  components: {
    MaterialIcon
  },
  data() {
    return {
      showLevels: ["EMER", "ALRT", "CRIT", "ERR", "WARN"],
    }
  },
  computed: {
    levels() { return Object.keys(iconLookup); },
    mungedLogs() {
      let newLogs = [];
      for (let log of this.indi.logs) {
        const msgLevel = log.message.slice(0, 4).trim();
        if (this.showLevels.indexOf(msgLevel) == -1) {
          continue;
        }
        const newLog = {
          level: msgLevel,
          message: log.message.slice(4),
          icon: iconLookup.hasOwnProperty(msgLevel) ? iconLookup[msgLevel] : "help",
          device: log.device,
          timestamp: log.timestamp.slice(0, 19),
        };
        newLogs.splice(0, 0, newLog);
      }
      return newLogs;
    }
  }
}
</script>