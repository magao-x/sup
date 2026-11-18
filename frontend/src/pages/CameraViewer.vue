<template>
  <div class="camera-viewer">
    <form class="viewer-toolbar" @submit.prevent="submit">
      <label for="shmim-name">Camera</label>
      <input id="shmim-name" v-model.trim="entered" placeholder="shmim name, e.g. camwfs" />
      <button class="btn" type="submit">Watch</button>
    </form>
    <div class="viewer-panel">
      <shmim-camera v-if="name" :key="name" :name="name"></shmim-camera>
      <div v-else class="hint">Enter the name of a camera's shmim to watch it.</div>
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

// The camera to watch is in the URL, camera.html?name=camwfs, so a view can
// be bookmarked or opened in a window of its own.
function nameFromUrl() {
  return new URLSearchParams(window.location.search).get('name') || '';
}

export default {
  components: { ShmimCamera },
  data() {
    const name = nameFromUrl();
    return { name, entered: name };
  },
  watch: {
    name: {
      immediate: true,
      handler(name) {
        document.title = name ? `${name} – camera` : 'Camera';
      },
    },
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
      this.name = this.entered = nameFromUrl();
    },
  },
};
</script>
