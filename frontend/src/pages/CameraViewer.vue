<template>
  <div class="camera-viewer">
    <form v-if="!popup" class="viewer-toolbar" @submit.prevent="submit">
      <label for="shmim-name">Camera</label>
      <input id="shmim-name" v-model.trim="entered" list="known-streams" placeholder="shmim name, e.g. camwfs" />
      <datalist id="known-streams">
        <option v-for="stream in catalog?.streams ?? []" :key="stream.name" :value="stream.name"></option>
      </datalist>
      <button class="btn" type="submit">Watch</button>
    </form>
    <div class="viewer-panel">
      <shmim-camera
        v-if="name && catalogLoaded"
        :key="name"
        :name="name"
        :dark="companions.dark"
        :saturation="companions.saturation"
        :saturation-level="companions.saturationLevel"
      ></shmim-camera>
      <div v-else-if="!name" class="hint">Enter the name of a camera's shmim to watch it.</div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.camera-viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-normal);
}
.viewer-toolbar {
  display: flex;
  align-items: center;
  gap: $medgap $lggap;
  padding: $lggap $unit;
  background: var(--inset-bg);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  label {
    font-weight: bold;
  }
  input {
    padding: 0.3em 0.6em;
    width: 16em;
  }
}
.viewer-panel {
  flex: 1;
  min-height: 0;
}
.hint {
  padding: $unit;
  color: var(--fg-inactive);
}
</style>

<script>
import ShmimCamera from "@/components/viewcam/ShmimCamera.vue";
import { companionsFor, fetchStreamCatalog } from "@/components/viewcam/streams.js";

// The camera to watch is in the URL, camera.html?name=camwfs, so a view can
// be bookmarked or opened in a window of its own. The streams tab opens it
// with popup=1, for a window that is all camera: no toolbar to pick another.
function paramsFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return { name: params.get('name') || '', popup: params.get('popup') === '1' };
}

export default {
  components: { ShmimCamera },
  data() {
    const { name, popup } = paramsFromUrl();
    return {
      name,
      entered: name,
      popup,
      catalog: null,
      catalogLoaded: false,
    };
  },
  computed: {
    companions() {
      return companionsFor(this.catalog, this.name);
    },
  },
  watch: {
    name: {
      immediate: true,
      handler(name) {
        document.title = name ? `${name} – camera` : 'Camera';
      },
    },
  },
  async created() {
    try {
      this.catalog = await fetchStreamCatalog();
    } catch (err) {
      // Without the list, the camera is shown without a dark or saturation mask.
      console.warn("Couldn't fetch the stream catalog:", err);
    }
    this.catalogLoaded = true;
  },
  mounted() {
    window.addEventListener('popstate', this.onPopState);
  },
  beforeUnmount() {
    window.removeEventListener('popstate', this.onPopState);
  },
  methods: {
    submit() {
      if (!this.entered || this.entered === this.name) return;
      const url = new URL(window.location.href);
      url.searchParams.set('name', this.entered);
      window.history.pushState(null, '', url);
      this.name = this.entered;
    },
    onPopState() {
      ({ name: this.name, popup: this.popup } = paramsFromUrl());
      this.entered = this.name;
    },
  },
};
</script>
