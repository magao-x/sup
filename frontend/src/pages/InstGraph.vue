<template>
  <div class="graph-wrapper" style="height: 100%">
    <div class="graph-controls" style="height: 500px;" ref="graphControls">
      <div class="graph-container" ref="graphContainer"></div>
      <div class="graph-buttons">
        <button>+</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.graph-controls {
  overflow: hidden;
  display: flex;
  flex-direction: row;
  height: 100%;
}

.graph-container {
  flex: 1;
  overflow: hidden;
}

.graph-buttons {
  width: 5em;
}
</style>
<script>
import * as ElementQueries from "css-element-queries";
import {
  constants,
  DomHelpers,
  getDefaultPlugins,
  Graph,
  InternalEvent,
  ModelXmlSerializer,
  RubberBandHandler,
} from '@maxgraph/core';
import utils from "@/utils.js";

export default {
  data() {
    return {
      graph: null,
    };
  },
  computed: {
    // Bumped by the server over the websocket whenever the watched .drawio
    // file is replaced on disk; watching it is what drives live reloading.
    instGraphRev() {
      return this.$store.state.instGraphRev;
    }
  },
  watch: {
    instGraphRev(newValue, oldValue) {
      if (newValue === null || newValue === oldValue) {
        return;
      }
      this.loadGraph();
    }
  },
  methods: {
    async loadDrawio() {
      try {
        // The file is replaced wholesale, so the URL alone doesn't identify
        // its contents; tag the request with the revision to defeat caching.
        const rev = this.instGraphRev || Date.now();
        const destURL = utils.buildBackendUrl(`instgraph.drawio?rev=${encodeURIComponent(rev)}`);
        const response = await fetch(destURL, { cache: "no-store" });
        if (!response.ok) {
          console.error("Error loading instrument state graph:", response.status, response.statusText);
          return null;
        }
        return response.text();
      } catch (error) {
        console.error("Error loading file:", error);
      }
    },
    extractDiagramContent(fileContent) {
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(fileContent, "text/xml");

      // Get <diagram> tags
      const diagramNodes = xmlDoc.querySelectorAll("diagram");

      if (diagramNodes.length === 0) {
        console.error("No <diagram> tag found in the XML.");
        return;
      }

      if (diagramNodes.length > 1) {
        console.warn(
          `Multiple <diagram> tags found (${diagramNodes.length}). Using the first one.`
        );
      }

      // Default to the first <diagram> tag's content
      return diagramNodes[0].innerHTML.trim();
    },
    initializeGraph() {
      const container = this.$refs.graphContainer;
      // Disables the built-in context menu
      InternalEvent.disableContextMenu(container);

      // Creates the graph inside the given container
      this.graph = new Graph(container, undefined, [
        ...getDefaultPlugins(),
        RubberBandHandler, // Enables rubber band selection
      ]);
      this.graph.setPanning(true); // Use mouse right button for panning
      // Folding would draw an expand/collapse icon on every group, fetched
      // from maxGraph's image base path, where we ship no images (hence a 404
      // for /expanded.gif on every render). The graph is a status display;
      // nothing in it needs collapsing. A new object, because the defaults
      // object is shared through the Graph prototype.
      this.graph.options = { ...this.graph.options, foldingEnabled: false };
    },
    async loadGraph() {
      const fileContent = await this.loadDrawio();
      if (!fileContent) {
        return;
      }
      const instrumentGraphDocument = this.extractDiagramContent(fileContent);
      if (!instrumentGraphDocument) {
        return;
      }
      const modelXmlSerializer = new ModelXmlSerializer(this.graph.model);
      this.graph.view.rendering = false;
      this.graph.getDataModel().batchUpdate(() => {
        this.graph.model.clear();
        modelXmlSerializer.import(instrumentGraphDocument);
      });
      this.graph.view.rendering = true;
      // this.graph.fit(0, false, 100);
      this.graph.fit(0, false, 100, true, false, false, this.$el.offsetHeight);
      this.graph.refresh();
    },
    fitGraph() {
      this.$refs.graphControls.style.height = `${this.$el.offsetHeight}px`;
      this.graph.fit(0, false, 100, true, false, false, this.$el.offsetHeight);
      this.graph.refresh();
    }
  },
  async mounted() {
    this.resizeSensor = new ElementQueries.ResizeSensor(this.$el, () => this.fitGraph());
    this.initializeGraph();
    this.loadGraph();
    this.fitGraph();
  },
  beforeUnmount: function () {
    this.resizeSensor.detach();
  }
};
</script>