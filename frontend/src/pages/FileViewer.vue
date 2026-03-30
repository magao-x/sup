<template>
  <div class="file-viewer">
    <div class="viewer-toolbar">
      <div class="viewer-title">{{ fileName }}</div>
      <div class="viewer-actions">
        <button class="btn" :class="{ active: activeTab === 'image' }" @click="activeTab = 'image'">
          <i class="material-icons">image</i> Image
        </button>
        <button class="btn" :class="{ active: activeTab === 'header' }" @click="activeTab = 'header'">
          <i class="material-icons">list</i> Header
        </button>
        <button class="btn" @click="downloadFile">
          <i class="material-icons">get_app</i> Download
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading FITS data…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-show="!loading && !error && activeTab === 'image'" class="viewer-panel">
      <div id="viewarr-container" ref="viewarrContainer" class="viewarr-container"></div>
    </div>

    <div v-if="!loading && !error && activeTab === 'header'" class="header-panel">
      <div class="header-filter">
        <input v-model="headerFilter" placeholder="Filter keywords…" />
      </div>
      <div class="header-tables">
        <div v-for="hdu in headerData" :key="hdu.hdu" class="hdu-section">
          <h3>HDU {{ hdu.hdu }}<span v-if="hdu.name"> — {{ hdu.name }}</span></h3>
          <table class="header-table">
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Value</th>
                <th>Comment</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(card, idx) in filteredCards(hdu.cards)" :key="idx">
                <td class="kw">{{ card.keyword }}</td>
                <td class="val">{{ card.value }}</td>
                <td class="cmt">{{ card.comment }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.file-viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-normal);
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $lggap $unit;
  background: var(--inset-bg);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.viewer-title {
  font-weight: bold;
  font-size: 1.1em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 1em;
}

.viewer-actions {
  display: flex;
  gap: $medgap;
  flex-shrink: 0;
  .btn {
    display: flex;
    align-items: center;
    gap: 0.3em;
    .material-icons {
      font-size: 18px;
    }
  }
}

.loading, .error {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2em;
}

.error {
  color: $danger-red;
}

.viewer-panel {
  flex: 1;
  position: relative;
  min-height: 0;
}

.viewarr-container {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.header-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header-filter {
  padding: $lggap $unit;
  flex-shrink: 0;
  input {
    width: 100%;
    max-width: 30em;
    padding: 0.4em 0.6em;
  }
}

.header-tables {
  flex: 1;
  overflow-y: auto;
  padding: 0 $unit $unit;
}

.hdu-section {
  margin-bottom: 1.5em;
  h3 {
    margin: 0.5em 0;
    color: $plasma-blue;
    font-size: 1em;
  }
}

.header-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
  font-family: monospace;

  th {
    text-align: left;
    padding: 0.3em 0.6em;
    border-bottom: 2px solid var(--border);
    color: var(--fg-inactive);
    position: sticky;
    top: 0;
    background: var(--bg-normal);
  }

  td {
    padding: 0.2em 0.6em;
    border-bottom: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
  }

  .kw {
    color: $plasma-blue;
    width: 12em;
  }

  .val {
    max-width: 25em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cmt {
    color: var(--fg-inactive);
  }
}
</style>

<script>
import utils from "@/utils.js";
import { createViewer, setImageData, destroyViewer, hasViewer } from "viewarr";

export default {
  data() {
    return {
      filePath: '',
      loading: true,
      error: null,
      activeTab: 'image',
      headerData: [],
      headerFilter: '',
      imageWidth: 0,
      imageHeight: 0,
      viewerReady: false,
    };
  },
  computed: {
    fileName() {
      if (!this.filePath) return '';
      return this.filePath.split('/').pop();
    },
  },
  methods: {
    filteredCards(cards) {
      if (!this.headerFilter) return cards;
      const f = this.headerFilter.toLowerCase();
      return cards.filter(c =>
        c.keyword.toLowerCase().includes(f) ||
        String(c.value).toLowerCase().includes(f) ||
        c.comment.toLowerCase().includes(f)
      );
    },

    async loadFile() {
      this.loading = true;
      this.error = null;

      try {
        // Load image data and header in parallel
        const [imageResp, headerResp] = await Promise.all([
          fetch(utils.buildBackendUrl(`obs/file?path=${encodeURIComponent(this.filePath)}`)),
          fetch(utils.buildBackendUrl(`obs/header?path=${encodeURIComponent(this.filePath)}`)),
        ]);

        if (!imageResp.ok) {
          throw new Error(`Failed to load image: ${imageResp.status}`);
        }
        if (!headerResp.ok) {
          throw new Error(`Failed to load header: ${headerResp.status}`);
        }

        this.headerData = await headerResp.json();

        // Parse binary image response: 8-byte header (u32 width, u32 height) + float32 pixels
        const arrayBuf = await imageResp.arrayBuffer();
        const headerView = new DataView(arrayBuf, 0, 8);
        this.imageWidth = headerView.getUint32(0, true);
        this.imageHeight = headerView.getUint32(4, true);
        // Slice to get a standalone ArrayBuffer of just the pixel data
        const pixelBuf = arrayBuf.slice(8);

        this.loading = false;

        // Wait for DOM update then init viewer
        await this.$nextTick();
        await this.initViewer(pixelBuf);
      } catch (e) {
        this.error = e.message || 'Failed to load file';
        this.loading = false;
      }
    },

    async initViewer(pixelBuf) {
      const containerId = 'viewarr-container';
      try {
        await createViewer(containerId);
        this.viewerReady = true;
        setImageData(containerId, pixelBuf, this.imageWidth, this.imageHeight, 'f32');
      } catch (e) {
        console.error('Failed to initialize viewer:', e);
        this.error = 'Failed to initialize image viewer: ' + e.message;
      }
    },

    downloadFile() {
      const url = utils.buildBackendUrl(`obs/download?path=${encodeURIComponent(this.filePath)}`);
      const a = document.createElement('a');
      a.href = url;
      a.download = this.fileName;
      a.click();
    },

    cleanup() {
      if (this.viewerReady && hasViewer('viewarr-container')) {
        destroyViewer('viewarr-container');
        this.viewerReady = false;
      }
    },
  },

  mounted() {
    const params = new URLSearchParams(window.location.search);
    this.filePath = params.get('path') || '';
    if (this.filePath) {
      this.loadFile();
    } else {
      this.loading = false;
      this.error = 'No file path specified';
    }
  },

  beforeDestroy() {
    this.cleanup();
  },
};
</script>
