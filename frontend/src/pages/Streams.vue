<template>
  <div class="streams">
    <div class="streams-header">
      <input v-model.trim="filter" type="search" placeholder="Filter streams" class="filter" />
      <span v-if="catalog" class="count">{{ countLabel }}</span>
    </div>

    <div v-if="blocked" class="blocked-hint">
      <i class="material-icons">block</i>
      <div>
        Your browser blocked the window for <strong>{{ blocked }}</strong>.
        To open cameras in windows of their own, allow pop-ups for this site:
        look for the blocked pop-up icon at the end of the address bar.
        Or <a :href="cameraUrl(blocked)" target="_blank" @click="blocked = null">open {{ blocked }} in a new tab</a>.
      </div>
      <button class="dismiss" type="button" title="Dismiss" @click="blocked = null">
        <i class="material-icons">close</i>
      </button>
    </div>

    <div v-if="error" class="error-message">Couldn't load the list of streams: {{ error }}</div>
    <div v-else-if="!catalog" class="loading-message">Loading…</div>
    <div v-else class="listing">
      <section v-for="group in groups" :key="group.title">
        <h3>{{ group.title }} <span class="count">{{ group.streams.length }}</span></h3>
        <table v-if="group.streams.length">
          <thead v-if="group.configured">
            <tr>
              <th>stream</th>
              <th>dark</th>
              <th>saturation mask</th>
              <th>saturates at</th>
              <th>rtimv config</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stream in group.streams" :key="stream.name">
              <td class="name">
                <a :href="cameraUrl(stream.name)" target="_blank" @click.prevent="open(stream.name)" title="Open in a new window">
                  <i class="material-icons">open_in_new</i>{{ stream.name }}
                </a>
              </td>
              <template v-if="group.configured">
                <td>{{ stream.dark ?? '—' }}</td>
                <td>{{ stream.sat_mask ?? '—' }}</td>
                <td>{{ stream.sat_level ?? '—' }}</td>
                <td class="config">{{ stream.config }}</td>
              </template>
            </tr>
          </tbody>
        </table>
        <div v-else class="none">None{{ filter ? ' match' : '' }}.</div>
      </section>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.streams {
  padding: $unit;
  box-sizing: border-box;
}
.streams-header {
  display: flex;
  align-items: center;
  gap: $unit;
  padding: $lggap $unit;
  background: var(--inset-bg);
  border: 1px solid var(--border);
  margin-bottom: $lggap;
  .filter {
    padding: 0.3em 0.6em;
    width: 18em;
  }
}
.count {
  color: var(--fg-inactive);
  font-size: 0.9em;
  font-weight: normal;
}
.blocked-hint {
  display: flex;
  align-items: flex-start;
  gap: $lggap;
  padding: $lggap $unit;
  margin-bottom: $lggap;
  border: 1px solid $beware-orange;
  background: color-mix(in srgb, $beware-orange 12%, transparent);
  a {
    color: $plasma-blue;
  }
  > .material-icons {
    color: $beware-orange;
  }
  > div {
    flex: 1;
  }
  .dismiss {
    border: none;
    background: none;
    color: inherit;
    cursor: pointer;
    padding: 0;
  }
}
.loading-message, .error-message, .none {
  padding: $unit;
  color: var(--fg-inactive);
}
.error-message {
  color: $danger-red;
}
section {
  margin-bottom: $unit;
}
h3 {
  margin: $lggap 0;
}
table {
  border-collapse: collapse;
  width: 100%;
  background: var(--inset-bg);
  border: 1px solid var(--border);
  font-family: monospace;
}
th {
  text-align: left;
  font-family: sans-serif;
  font-weight: normal;
  color: var(--fg-inactive);
}
th, td {
  padding: 0.3rem 0.8rem;
  border-bottom: 1px solid color-mix(in srgb, var(--border) 30%, transparent);
}
tbody tr:hover {
  background: color-mix(in srgb, $plasma-blue 15%, transparent);
}
td.name a {
  color: $plasma-blue;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  &:hover {
    text-decoration: underline;
  }
  .material-icons {
    font-size: 1.1em;
  }
}
td.config {
  color: var(--fg-inactive);
}
</style>

<script>
import { cameraUrl, fetchStreamCatalog, openCameraPopup } from "@/components/viewcam/streams.js";

export default {
  data() {
    return {
      catalog: null,
      error: null,
      filter: '',
      // The stream whose window was last blocked, if any.
      blocked: null,
    };
  },
  computed: {
    matching() {
      const filter = this.filter.toLowerCase();
      return this.catalog.streams.filter((stream) => stream.name.toLowerCase().includes(filter));
    },
    groups() {
      return [
        { title: 'Cameras and DMs', configured: true, streams: this.matching.filter((s) => s.config) },
        { title: 'Other shmims', configured: false, streams: this.matching.filter((s) => !s.config) },
      ];
    },
    countLabel() {
      const total = this.catalog.streams.length;
      return this.filter ? `${this.matching.length} of ${total} streams` : `${total} streams`;
    },
  },
  async created() {
    try {
      this.catalog = await fetchStreamCatalog();
    } catch (err) {
      this.error = err.message;
    }
  },
  methods: {
    cameraUrl,
    open(name) {
      this.blocked = openCameraPopup(name) ? null : name;
    },
  },
};
</script>
