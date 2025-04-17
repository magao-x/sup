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
  props: {
    relativeURL: String,
    // n.b. this can be anything, we just snoop on updates
    // to know when to re-fetch the graph
    lastUpdated: {
      type: String,
      default: "",
    }
  },
  watch: {
    async lastUpdated(newValue, oldValue) {
      this.loadGraph();
    }
  },
  methods: {
    async loadDrawio() {
      try {
        const destURL = utils.buildBackendUrl(`instgraph`);
        const response = await fetch(destURL);
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
    },
    async loadGraph() {
      const fileContent = await this.loadDrawio();
      const instrumentGraphDocument = this.extractDiagramContent(fileContent);
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