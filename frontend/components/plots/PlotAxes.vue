<template>
  <div class="axes-container">
    <svg class="axes" />
  </div>
</template>
<style lang="scss" scoped>
.axes-container {
  flex: 1;
  min-width: 300px;
  min-height: 200px;
  max-height: 1200px;
  max-width: 1200px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.axes {
  max-width: 100%;
  max-height: 100%;
  flex: 1;
}
</style>
<script>
import { DateTime } from "luxon";
import * as ElementQueries from "css-element-queries";
import * as d3 from "d3";
import constants from "./constants.js";

const tickSpacing = 40;

export default {
  props: {
    dataColors: {
      type: Array,
      default: function() {
        return constants.colorCycle;
      }
    },
    axisColor: {
      type: String,
      default: function() {
        return constants.axisColor;
      }
    },
    markerSize: {
      type: Number,
      default: function() {
        return 2;
      }
    },
    timeSeries: {
      type: Boolean,
      default: function() {
        return false;
      }
    },
    numMinutes: {
      type: Number,
      default: function () { return null; }
    },
    data: {
      type: Object,
      default: function() {
        return {
          xsquared: {
            points: [
              { x: 0, y: 0 },
              { x: 1, y: 1 },
              { x: 2, y: 4 },
              { x: 3, y: 9 },
              { x: 4, y: 16 }
            ]
          }
        };
      }
    }
  },
  watch: {
    data: {
      handler(newValue, oldValue) {
        this.updatePlot();
      },
      deep: true,
    }
  },
  inject: ["time"],
  methods: {
    computeDomain(accessor) {
      let dataEntries = Object.entries(this.data);
      if (!dataEntries[0][1].points.length) return [0, 1];

      // take first point of first line as initial min/max vals
      let valMin = accessor(dataEntries[0][1].points[0]),
        valMax = accessor(dataEntries[0][1].points[0]);

      // loop over points in all lines
      for (let [name, lineData] of dataEntries) {
        let [newValMin, newValMax] = d3.extent(lineData.points, accessor);
        if (newValMin < valMin) {
          valMin = newValMin;
        }
        if (newValMax > valMax) {
          valMax = newValMax;
        }
      }
      return [valMin, valMax];
    },
    hashString(input) {
      let hash = 0;
      if (input.length == 0) {
        return hash;
      }
      for (let i = 0; i < input.length; i++) {
        let char = input.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash = hash & hash; // Convert to 32bit integer
      }
      return hash;
    },
    updatePlot() {
      // Calculate plot dimensions in screen coords from margins
      // and element dimensions in screen coords
      var margin = { top: 10, right: 30, bottom: 50, left: 50 };
      const selector = 'svg.axes';
      const width = this.$el.clientWidth - margin.left - margin.right;
      const height = this.$el.clientHeight - margin.top - margin.bottom;
      let xGetter;
      let yGetter = d => d.y;
      let xDomain;
      if (this.timeSeries) {
        xGetter = d => d3.isoParse(d.x);
        if (this.numMinutes !== null) {
          const startTime = this.time.currentTime.minus({minutes: this.numMinutes});
          xDomain = [startTime, this.time.currentTime];
        } else {
          xDomain = this.computeDomain(xGetter);
        }
        this.xScale = d3
          .scaleTime()
          .domain(xDomain)
          .range([0, width]);
      } else {
        xGetter = d => d.x;
        xDomain = this.computeDomain(xGetter);
        this.xScale = d3
          .scaleLinear()
          .domain(xDomain) // input
          .range([0, width]); // output
      }

      let yDomain = this.computeDomain(yGetter);

      this.yScale = d3
        .scaleLinear()
        .domain(yDomain) // input
        .range([height, 0]); // output

      // 7. d3's line generator
      this.line = d3
        .line()
        .x(d => this.xScale(xGetter(d))) // set the x values for the line generator
        .y(d => this.yScale(yGetter(d))); // set the y values for the line generator
      // .curve(d3.curveMonotoneX); // apply smoothing to the line

      // Create the svg element, removing an existing one if necessary
      d3.select(this.$el)
        .select(selector)
        .remove();
      this.d3svg = d3
        .select(this.$el)
        .append("svg")
        .attr('class', 'axes')
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

      // 3. Call the x axis in a group tag
      var xAxis = this.d3svg
        .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .style("color", this.axisColor)
        .call(d3.axisBottom(this.xScale).ticks(width / tickSpacing)); // Create an axis component with d3.axisBottom

      // 4. Call the y axis in a group tag
      var yAxis = this.d3svg
        .append("g")
        .attr("class", "y axis")
        .style("color", this.axisColor)
        .call(d3.axisLeft(this.yScale).ticks(height / tickSpacing)); // Create an axis component with d3.axisLeft

      let idx = 0;
      for (let [name, dataset] of Object.entries(this.data)) {
        // 9. Append the path, bind the data, and call the line generator
        this.d3svg
          .append("path")
          .datum(dataset.points) // 10. Binds data to the line
          // .classed("line", true) // Assign a class for styling
          .style("fill", "none")
          .style("stroke-width", 1)
          .style("stroke", this.dataColors[idx])
          .attr("d", this.line); // 11. Calls the line generator

        // 12. Appends a circle for each datapoint
        // this.d3svg
        //   .selectAll(`.dot.line-${this.hashString(name)}`)
        //   .data(dataset.points)
        //   .enter()
        //   .append("circle") // Uses the enter().append() method
        //   .classed("dot", true) // Assign a class for styling
        //   .style("fill", this.dataColors[idx])
        //   .attr("cx", d => this.xScale(xGetter(d)))
        //   .attr("cy", d => this.yScale(yGetter(d)))
        //   .attr("r", this.markerSize);
        idx = (idx + 1) % this.dataColors.length;
      }
    }
  },
  mounted: function() {
    this.updatePlot();
    this.resizeSensor = new ElementQueries.ResizeSensor(this.$el, () =>
      this.updatePlot()
    );
  },
  beforeDestroy: function() {
    this.resizeSensor.detach();
  }
};
</script>