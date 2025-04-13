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
// import elk from "cytoscape-elk";
// import nodeHtmlLabel from "cytoscape-node-html-label";
import dagre from 'cytoscape-dagre';

cytoscape.use( dagre );
import utils from '@/utils.js';

// cytoscape.use(elk);
// nodeHtmlLabel(cytoscape);
// import tidytree from "cytoscape-tidytree";
// cytoscape.use(tidytree);

function nameToColor(name) {
  if (/^cam.+/.test(name)) {
    return "#f39c1f";
  } else if(/^stage.+/.test(name)) {
    return "#bdc3c7";
  } else if (/.+ttm$/.test(name) || /^ttm.+/.test(name)) {
    return "#f47750";
  } else if (/^dm.+/.test(name)) {
    return "#c0392b";
  } else if (/^fw.+/.test(name)) {
    return "#2ecc71";
  } else if (/^flip.+/.test(name)) {
    return "#9b59b6";
  } else {
    return "#77797d";
  }
}

export default Vue.extend({
  data() {
    return {
      lightPath: null,
    };
  },
  methods: {
    async getAllData() {
      try {
        const destURL = utils.buildBackendUrl('light-path');
        const res = await fetch(destURL);
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
      // layout: {
      //   name: "elk",
      //   elk: {
      //     algorithm: "layered",
      //     // "elk.direction": "RIGHT",
      //     // 'elk.alignment': 'TOP',
      //     // 'elk.layered.thoroughness': 1,
      //     'elk.layered.nodePlacement.bk.fixedAlignment': 'LEFTDOWN',
      //     // 'elk.layered.nodePlacement.favorStraightEdges': true,
      //     // 'elk.layered.layering.strategy': 'STRETCH_WIDTH',
      //     // "elk.layered.nodePlacement.strategy": "SIMPLE",
      //     // 'elk.layered.compaction.postCompaction.strategy': 'LEFT',
      //     // 'elk.layered.priority.straightness': 10000000,
      //     'elk.edgeRouting': 'ORTHOGONAL',
      //     'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
      //     'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX'
      //   },
      //   // some more options here...
      // },
      layout: {
        name: 'dagre',
        rankDir: "UD",
        // rankDir: "LR",
      },
      style: [
        {
          selector: "node",
          style: {
            // "background-color": "#dd4de2",
            "background-color": function(ele){return nameToColor(ele.data().label);},
            label: "data(id)",
            'text-valign': 'center',
            'text-halign': 'center',
            width: 120,
            shape: "rectangle",
          },
        },

        {
          selector: "edge",
          style: {
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "line-color": "#77797d",
            "target-arrow-color": "#77797d",
            opacity: 0.5,
          },
        },
      ],
      elements: elements,
    });
    // cy.nodeHtmlLabel([{
    //   query: '.nodeIcon',
    //   halign: 'center',
    //   valign: 'center',
    //   halignBox: 'center',
    //   valignBox: 'center',
    //   tpl: (data) => {
    //     return "<b>" + data.label + "</b>";
    //   }
    // }]);
  },
});
</script>