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
<script>
import Vue from "vue";
import cytoscape from "cytoscape";
import elk from "cytoscape-elk";
import nodeHtmlLabel from "cytoscape-node-html-label";

cytoscape.use(elk);
nodeHtmlLabel(cytoscape);

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
          ":" + "8000";
        // String(window.location.port);
        const res = await fetch(`${baseURL}/light-path`);
        if (!res.ok) {
          const message = `An error has occured: ${res.status} - ${res.statusText}`;
          throw new Error(message);
        }
        const data = await res.json();
        console.log(Object.keys(data));
        this.lightPath = data;
      } catch (err) {
        console.error(err);
        this.lightPath = null;
      }
    },
  },
  async mounted() {
    await this.getAllData();
    console.log(this.lightPath);
    



    let elements = [
      //: { data: GraphEdge | GraphNode, group: string, grabbable: false }[]
      // {
      //   data: { id: "first", label: "first" },
      //   group: "nodes",
      //   grabbable: false,
      // },
      // {
      //   data: { id: "second", label: "second" },
      //   group: "nodes",
      //   grabbable: false,
      // },
      // {
      //   data: { id: "edge-first-second", source: "first", target: "second" },
      //   group: "edges",
      //   grabbable: false,
      // },
    ];

    for (let device of Object.keys(this.lightPath)) {
      console.log(device, this.lightPath[device]);
      elements.push({
        data: { id: device, label: device },
        group: "nodes", grabbable: false,
        classes: 'nodeIcon'
      })
      const depends = this.lightPath[device].in;
      if (typeof depends === "undefined") {
        continue;
      }
      for (let input of depends) {
        elements.push({
          data: { id: `edge-${device}-${input}`, source: input, target: device },
          group: "edges",
          grabbable: false,
        });
      }
    }
    let cy = cytoscape({
      container: this.$el,

      // demo your layout
      layout: {
        name: "elk",
        elk: {
          algorithm: "layered",
          // "elk.direction": "RIGHT",
          // 'elk.alignment': 'TOP',
          // 'elk.layered.thoroughness': 1,
          'elk.layered.nodePlacement.bk.fixedAlignment': 'LEFTDOWN',
          // 'elk.layered.nodePlacement.favorStraightEdges': true,
          // 'elk.layered.layering.strategy': 'STRETCH_WIDTH',
          // "elk.layered.nodePlacement.strategy": "SIMPLE",
          // 'elk.layered.compaction.postCompaction.strategy': 'LEFT',
          // 'elk.layered.priority.straightness': 10000000,
          'elk.edgeRouting': 'ORTHOGONAL',
        },
        // some more options here...
      },

      style: [
        {
          selector: "node",
          style: {
            "background-color": "#dd4de2",
            // label: "data(id)",
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
      elements: elements,
    });
    cy.nodeHtmlLabel([{
      query: '.nodeIcon',
      halign: 'center',
      valign: 'center',
      halignBox: 'center',
      valignBox: 'center',
      tpl: (data) => {
        return "<b>" + data.label + "</b>";
      }
    }]);
  },
});
</script>