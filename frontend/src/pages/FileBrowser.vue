<template>
  <div class="file-browser" :class="{ 'log-collapsed': !logOpen }">
    <div class="browser-header">
      <div class="breadcrumb">
        <span class="crumb clickable" @click="navigateTo('')">obs</span>
        <template v-for="(seg, idx) in pathSegments" :key="idx">
          <span class="separator">/</span>
          <span class="crumb clickable" @click="navigateTo(pathSegments.slice(0, idx + 1).join('/'))">{{ seg }}</span>
        </template>
      </div>
      <div class="browser-info" v-if="listing">
        <span>{{ listing.total }} items</span>
      </div>
    </div>

    <!-- Journal log panel -->
    <div class="log-panel" :class="{ open: logOpen }">
      <div class="log-header" @click="logOpen = !logOpen">
        <i class="material-icons log-toggle">{{ logOpen ? 'expand_more' : 'expand_less' }}</i>
        <span class="log-title">Journal Log</span>
        <span class="log-status" :class="logConnected ? 'connected' : 'disconnected'">
          {{ logConnected ? 'live' : 'disconnected' }}
        </span>
      </div>
      <div class="log-body" ref="logBody" v-show="logOpen">
        <div v-for="(line, i) in logLines" :key="i" class="log-line">{{ line }}</div>
      </div>
    </div>

    <div class="listing-container" ref="listContainer" @scroll="onScroll">
      <div v-if="loading && entries.length === 0" class="loading-message">Loading…</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <template v-else>
        <!-- virtual scroll spacer top -->
        <div :style="{ height: topSpacerHeight + 'px' }"></div>
        <div
          v-for="entry in visibleEntries"
          :key="entry.name"
          class="entry"
          :class="{ 'is-dir': entry.is_dir }"
          @click="onEntryClick(entry)"
        >
          <i class="material-icons entry-icon">{{ entry.is_dir ? 'folder' : 'insert_drive_file' }}</i>
          <span class="entry-name">{{ entry.name }}</span>
          <span class="entry-size" v-if="!entry.is_dir">{{ formatSize(entry.size) }}</span>
          <span class="entry-mtime">{{ formatDate(entry.mtime) }}</span>
        </div>
        <!-- virtual scroll spacer bottom -->
        <div :style="{ height: bottomSpacerHeight + 'px' }"></div>
        <!-- load-more trigger for pages beyond what's loaded -->
        <div v-if="hasMore && !loading" class="load-more" ref="loadMoreSentinel">
          <button class="btn" @click="loadMore">Load more…</button>
        </div>
        <div v-if="loading && entries.length > 0" class="loading-more">Loading…</div>
      </template>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@use "@/css/variables.scss" as *;

.file-browser {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: $unit;
  box-sizing: border-box;
}

.browser-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $lggap $unit;
  background: var(--inset-bg);
  border: 1px solid var(--border);
  margin-bottom: $lggap;
}

.breadcrumb {
  font-size: 1.1em;
  .crumb.clickable {
    cursor: pointer;
    color: $plasma-blue;
    &:hover {
      text-decoration: underline;
    }
  }
  .separator {
    margin: 0 0.3em;
    color: var(--fg-inactive);
  }
}

.browser-info {
  color: var(--fg-inactive);
  font-size: 0.9em;
}

.listing-container {
  flex: 1;
  overflow-y: auto;
  border: 1px solid var(--border);
  background: var(--inset-bg);
  min-height: 0;
}

.entry {
  display: flex;
  align-items: center;
  padding: 0.3rem 0.8rem;
  cursor: pointer;
  height: 32px;
  box-sizing: border-box;
  border-bottom: 1px solid color-mix(in srgb, var(--border) 30%, transparent);

  &:hover {
    background: color-mix(in srgb, $plasma-blue 15%, transparent);
  }

  &.is-dir .entry-name {
    font-weight: bold;
  }
}

.entry-icon {
  font-size: 18px;
  margin-right: 0.5rem;
  color: var(--fg-inactive);
  .is-dir & {
    color: $icon-yellow;
  }
}

.entry-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.entry-size {
  width: 6em;
  text-align: right;
  margin-right: 1em;
  color: var(--fg-inactive);
  font-size: 0.9em;
}

.entry-mtime {
  width: 10em;
  text-align: right;
  color: var(--fg-inactive);
  font-size: 0.9em;
}

.loading-message, .error-message, .loading-more {
  text-align: center;
  padding: 2rem;
  color: var(--fg-inactive);
}

.error-message {
  color: $danger-red;
}

.load-more {
  text-align: center;
  padding: 0.5rem;
}

/* Journal log panel */
.log-panel {
  border: 1px solid var(--border);
  background: var(--inset-bg);
  margin-bottom: $lggap;
  display: flex;
  flex-direction: column;
  min-height: 32px;
  transition: flex-basis 0.15s ease;

  &.open {
    flex: 0 0 200px;
  }
}

.log-header {
  display: flex;
  align-items: center;
  padding: 0.3rem 0.6rem;
  cursor: pointer;
  gap: 0.4em;
  user-select: none;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--inset-bg) 80%, black);

  &:hover {
    background: color-mix(in srgb, $plasma-blue 10%, var(--inset-bg));
  }
}

.log-toggle {
  font-size: 18px;
  color: var(--fg-inactive);
}

.log-title {
  font-weight: bold;
  font-size: 0.9em;
}

.log-status {
  margin-left: auto;
  font-size: 0.75em;
  padding: 0.1em 0.5em;
  border-radius: 3px;
  text-transform: uppercase;
  font-weight: bold;

  &.connected {
    color: $verdant-green;
  }
  &.disconnected {
    color: var(--fg-inactive);
  }
}

.log-body {
  flex: 1;
  overflow-y: auto;
  font-family: monospace;
  font-size: 0.8em;
  line-height: 1.5;
  padding: 0.3rem 0.6rem;
}

.log-line {
  white-space: pre;
  color: var(--fg-inactive);
}
</style>

<script>
import utils from "@/utils.js";

const ROW_HEIGHT = 32;
const PAGE_SIZE = 200;
const OVERSCAN = 20;
const MAX_LOG_LINES = 1000;
const RECONNECT_DELAY_MS = 3000;

export default {
  data() {
    return {
      currentPath: '',
      entries: [],
      listing: null,
      loading: false,
      error: null,
      scrollTop: 0,
      containerHeight: 0,
      // Log panel state
      logOpen: true,
      logLines: [],
      logConnected: false,
      _logWs: null,
      _logReconnectTimer: null,
    };
  },
  computed: {
    pathSegments() {
      if (!this.currentPath) return [];
      return this.currentPath.split('/').filter(s => s);
    },
    hasMore() {
      if (!this.listing) return false;
      return this.entries.length < this.listing.total;
    },
    // Virtual scroll computations
    totalHeight() {
      return this.entries.length * ROW_HEIGHT;
    },
    startIndex() {
      return Math.max(0, Math.floor(this.scrollTop / ROW_HEIGHT) - OVERSCAN);
    },
    endIndex() {
      const visible = Math.ceil(this.containerHeight / ROW_HEIGHT);
      return Math.min(this.entries.length, Math.floor(this.scrollTop / ROW_HEIGHT) + visible + OVERSCAN);
    },
    visibleEntries() {
      return this.entries.slice(this.startIndex, this.endIndex);
    },
    topSpacerHeight() {
      return this.startIndex * ROW_HEIGHT;
    },
    bottomSpacerHeight() {
      return Math.max(0, (this.entries.length - this.endIndex) * ROW_HEIGHT);
    },
  },
  methods: {
    async fetchEntries(path, offset = 0) {
      this.loading = true;
      this.error = null;
      try {
        const url = utils.buildBackendUrl(`obs/list?path=${encodeURIComponent(path)}&offset=${offset}&limit=${PAGE_SIZE}`);
        const res = await fetch(url);
        if (!res.ok) {
          const detail = await res.text();
          throw new Error(`${res.status}: ${detail}`);
        }
        const data = await res.json();
        if (offset === 0) {
          this.entries = data.entries;
        } else {
          this.entries = this.entries.concat(data.entries);
        }
        this.listing = data;
      } catch (e) {
        this.error = e.message || 'Failed to load directory';
      } finally {
        this.loading = false;
      }
    },
    navigateTo(path) {
      this.currentPath = path;
      this.entries = [];
      this.listing = null;
      if (this.$refs.listContainer) {
        this.$refs.listContainer.scrollTop = 0;
      }
      this.fetchEntries(path);
    },
    onEntryClick(entry) {
      if (entry.is_dir) {
        const newPath = this.currentPath ? this.currentPath + '/' + entry.name : entry.name;
        this.navigateTo(newPath);
      } else if (/\.fits?$/i.test(entry.name)) {
        this.openFileViewer(entry);
      } else {
        this.downloadFile(entry);
      }
    },
    openFileViewer(entry) {
      const filePath = this.currentPath ? this.currentPath + '/' + entry.name : entry.name;
      const viewerUrl = `${window.location.origin}/viewer.html?path=${encodeURIComponent(filePath)}`;
      window.open(viewerUrl, `viewer_${filePath}`, 'width=1200,height=800');
    },
    downloadFile(entry) {
      const filePath = this.currentPath ? this.currentPath + '/' + entry.name : entry.name;
      const url = utils.buildBackendUrl(`obs/download?path=${encodeURIComponent(filePath)}`);
      const a = document.createElement('a');
      a.href = url;
      a.download = entry.name;
      a.click();
    },
    loadMore() {
      if (this.hasMore && !this.loading) {
        this.fetchEntries(this.currentPath, this.entries.length);
      }
    },
    onScroll() {
      if (!this.$refs.listContainer) return;
      this.scrollTop = this.$refs.listContainer.scrollTop;
      // Auto-load more when near bottom
      const el = this.$refs.listContainer;
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 200) {
        this.loadMore();
      }
    },
    updateContainerHeight() {
      if (this.$refs.listContainer) {
        this.containerHeight = this.$refs.listContainer.clientHeight;
      }
    },
    formatSize(bytes) {
      if (bytes == null) return '';
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
      if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
      return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
    },
    formatDate(epochSec) {
      if (!epochSec) return '';
      const d = new Date(epochSec * 1000);
      return d.toISOString().replace('T', ' ').substring(0, 19);
    },
    // -- Log panel WebSocket --
    connectLog() {
      if (this._logWs) return;
      const url = utils.buildWebSocketUrl('ws/logs');
      const ws = new WebSocket(url);
      ws.binaryType = 'arraybuffer';
      ws.onopen = () => {
        this.logConnected = true;
      };
      ws.onmessage = (evt) => {
        const text = typeof evt.data === 'string'
          ? evt.data
          : new TextDecoder().decode(evt.data);
        this.logLines.push(text);
        if (this.logLines.length > MAX_LOG_LINES) {
          this.logLines.splice(0, this.logLines.length - MAX_LOG_LINES);
        }
        this.$nextTick(() => {
          const el = this.$refs.logBody;
          if (el) el.scrollTop = el.scrollHeight;
        });
      };
      ws.onclose = () => {
        this.logConnected = false;
        this._logWs = null;
        this._scheduleReconnect();
      };
      ws.onerror = () => {
        ws.close();
      };
      this._logWs = ws;
    },
    disconnectLog() {
      clearTimeout(this._logReconnectTimer);
      if (this._logWs) {
        this._logWs.onclose = null;
        this._logWs.close();
        this._logWs = null;
      }
      this.logConnected = false;
    },
    _scheduleReconnect() {
      clearTimeout(this._logReconnectTimer);
      this._logReconnectTimer = setTimeout(() => this.connectLog(), RECONNECT_DELAY_MS);
    },
  },
  mounted() {
    this.fetchEntries('');
    this.updateContainerHeight();
    this._resizeObserver = new ResizeObserver(() => this.updateContainerHeight());
    if (this.$refs.listContainer) {
      this._resizeObserver.observe(this.$refs.listContainer);
    }
    this.connectLog();
  },
  beforeDestroy() {
    if (this._resizeObserver) {
      this._resizeObserver.disconnect();
    }
    this.disconnectLog();
  },
};
</script>
