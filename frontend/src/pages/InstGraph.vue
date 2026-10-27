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
  /* Nothing to interact with, so a drag shouldn't select label text either */
  user-select: none;
}

.graph-buttons {
  width: 5em;
}
</style>
<script>
import * as ElementQueries from "css-element-queries";
import {
  BaseGraph,
  EdgeMarker,
  EdgeMarkerRegistry,
  FitPlugin,
  InternalEvent,
  ModelXmlSerializer,
  Perimeter,
  PerimeterRegistry,
  registerElbowEdgeStyle,
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

      // The graph is a status display: nothing to select, drag, edit or
      // collapse. BaseGraph, unlike Graph, brings in no interaction plugins
      // and registers no style elements, which leaves the bundler free to
      // drop everything we don't name here.
      this.graph = new BaseGraph({ container, plugins: [FitPlugin] });
      this.graph.setEnabled(false);
      // Folding would draw an expand/collapse icon on every group, fetched
      // from maxGraph's image base path, where we ship no images (hence a 404
      // for /expanded.gif on every render).
      this.graph.options.foldingEnabled = false;
    },
    registerStyleElements() {
      // Only what the instrument graph's styles use. Rectangles and plain
      // connectors are maxGraph's fallbacks and need no registration; anything
      // else a future diagram names would silently render without it.
      PerimeterRegistry.add('rectanglePerimeter', Perimeter.RectanglePerimeter);
      EdgeMarkerRegistry.add('classic', EdgeMarker.createArrow(2));
      registerElbowEdgeStyle();
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
      const model = this.graph.getDataModel();
      // Tear down the drawing of the graph being replaced while its cells
      // are still reachable from the root. Left to the root change, maxGraph
      // keeps every old cell's state (and its SVG) alive when the change
      // happens with rendering off, so each reload stacked another copy.
      this.graph.view.clear(model.getRoot(), true, true);
      this.graph.view.rendering = false;
      // Importing replaces the root, so there is no need to clear first.
      new ModelXmlSerializer(model).import(instrumentGraphDocument);
      this.graph.view.rendering = true;
      this.fitToHeight();
    },
    fitGraph() {
      this.$refs.graphControls.style.height = `${this.$el.offsetHeight}px`;
      this.fitToHeight();
    },
    fitToHeight() {
      this.graph.getPlugin(FitPlugin.pluginId).fit({
        border: 0,
        margin: 100,
        maxHeight: this.$el.offsetHeight,
      });
      this.graph.refresh();
    }
  },
  async mounted() {
    this.resizeSensor = new ElementQueries.ResizeSensor(this.$el, () => this.fitGraph());
    this.registerStyleElements();
    this.initializeGraph();
    this.loadGraph();
    this.fitGraph();
  },
  beforeUnmount: function () {
    this.resizeSensor.detach();
  }
};
</script>