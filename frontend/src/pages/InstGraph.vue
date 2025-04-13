<template>
  <div ref="graphContainer" id="graph-container"></div>
</template>

<style scoped>
.graph-container {
  width: 100%;
  height: 500px;
  border: 1px solid #ccc;
}
</style>

<script>
import {
  constants,
  DomHelpers,
  getDefaultPlugins,
  Graph,
  InternalEvent,
  ModelXmlSerializer,
  RubberBandHandler,
} from '@maxgraph/core';
import utils2 from "@/utils.js";

export default {
  data() {
    return {
    //   instrumentGraph: null,
    };
  },
  props: {
    xmlData: String, // XML content from draw.io
  },
  computed: {
    insGraphUpdateTime() {
      return this.$store.state.instGraphUpdateTime;
    },
    instGraphFilename() {
      return this.$store.state.instGraphFilename;
    },
  },
  watch: {
    insGraphUpdateTime(newVal) {
      if (newVal) {
        console.log("Reloading graph from file:", this.instGraphFilename);
        this.loadGraph(this.instGraphFilename);
      }
    },
    instGraphFilename(newVal) {
      if (newVal) {
        console.log("Reloading graph from file:", this.instGraphFilename);
        this.loadGraph(this.instGraphFilename);
      }
    }
  },
  methods: {
    async loadDrawio(file) {
      try {
        const destURL = utils2.buildBackendUrl(`drawio-files/${file}`);
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
    async loadGraph(file) {
        const fileContent = await this.loadDrawio(file);
        const instrumentGraph = this.extractDiagramContent(fileContent);

        const initializeGraph = (container) => {
            // Disables the built-in context menu
            InternalEvent.disableContextMenu(container);

            const graph = new Graph(container, undefined, [
                ...getDefaultPlugins(),
                RubberBandHandler, // Enables rubber band selection
            ]);
            graph.setPanning(true); // Use mouse right button for panning

            const modelXmlSerializer = new ModelXmlSerializer(graph.model);
            // modelXmlSerializer.import(xmlWithVerticesAndEdges);
            modelXmlSerializer.import(instrumentGraph);

            // return graph;
        };

        // Creates the graph inside the given container
        const container = document.querySelector('#graph-container');
        container.innerHTML = "";
        const graph = initializeGraph(container);
    },
  },
  async mounted() {
    this.loadGraph(this.instGraphFilename);
  },
};
</script>