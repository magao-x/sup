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
            <td class="msg">{{ log.message }}</td>
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
@use "@/css/variables.scss" as *;

.levels {
  display: flex;
  width: 100%;

  .oneLevel {
    flex: 1;

    label {
      padding: 0 1em;
      font-family: monospace;
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
  width: 2000px;
  overflow-x: scroll;
}

tbody {
  font-family: monospace;
  font-size: 12px;
}

.timestamp {
  width: 6em;
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
  width: 11em;
}

</style>
<script>
import utils from "@/mixins/utils.js";
import MaterialIcon from "@/components/basic/MaterialIcon.vue";
import { LOG_LEVELS, logLevel } from "@/logLevels.js";

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
      showLevels: [...LOG_LEVELS],
    }
  },
  computed: {
    levels() { return LOG_LEVELS; },
    mungedLogs() {
      let newLogs = [];
      for (let log of this.indi.logs) {
        const msgLevel = logLevel(log);
        if (this.showLevels.indexOf(msgLevel) == -1) {
          continue;
        }
        const newLog = {
          level: msgLevel,
          message: log.message.slice(4),
          icon: iconLookup[msgLevel],
          device: log.device,
          timestamp: log.timestamp.slice(11, 19),
        };
        newLogs.push(newLog);
      }
      // Newest first
      return newLogs.reverse();
    }
  }
}
</script>