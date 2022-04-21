<template>
  <div class="cytoscape-graph"></div>
</template>
<style scoped>
.cytoscape-graph {
  min-width: 30em;
  min-height: 30em;
  width: 100%;
  height: 100%;
}
</style>
<script lang="ts">
import Vue from "vue";
import cytoscape from "cytoscape";
import elk from "cytoscape-elk";

cytoscape.use(elk);

export default Vue.extend({
  data() {
    return {
      lightPath: null,
    };
  },
  methods: {
    async getAllData() {
      try {
        const baseURL =
          window.location.protocol +
          "//" +
          window.location.hostname +
          ":" +
          String(window.location.port);
        const res = await fetch(`${baseURL}/light-path`);
        if (!res.ok) {
          const message = `An error has occured: ${res.status} - ${res.statusText}`;
          throw new Error(message);
        }
        const data = await res.json();
        this.lightPath = data;
      } catch (err) {
        this.lightPath = null;
      }
    },
  },
  async mounted() {
    await this.getAllData();
    cytoscape({
      container: this.$el,

      // demo your layout
      layout: {
        name: "elk",
        elk: {
          algorithm: "layered",
          "elk.direction": "RIGHT",
          // 'elk.alignment': 'TOP',
          // 'elk.layered.thoroughness': 1,
          // 'elk.layered.nodePlacement.bk.fixedAlignment': 'LEFTDOWN',
          // 'elk.layered.nodePlacement.favorStraightEdges': true,
          // 'elk.layered.layering.strategy': 'STRETCH_WIDTH',
          "elk.layered.nodePlacement.strategy": "SIMPLE",
          // 'elk.layered.compaction.postCompaction.strategy': 'LEFT',
          // 'elk.layered.priority.straightness': 10000000,
          // 'elk.edgeRouting': 'ORTHOGONAL',
        },
        // some more options here...
      },

      style: [
        {
          selector: "node",
          style: {
            "background-color": "#dd4de2",
            label: "data(id)",
          },
        },

        {
          selector: "edge",
          style: {
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "line-color": "#dd4de2",
            "target-arrow-color": "#dd4de2",
            opacity: 0.5,
          },
        },
      ],
      elements: [
        {
          data: { id: "first", label: "first" },
          group: "nodes",
          grabbable: false,
        },
        {
          data: { id: "second", label: "second" },
          group: "nodes",
          grabbable: false,
        },
        {
          data: { id: "edge-first-second", source: "first", target: "second" },
          group: "edges",
          grabbable: false,
        },
      ],
    });
  },
});
</script>