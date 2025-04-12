<template>
    <div>
        <iframe :src="src"></iframe>
        <a class="expandlink" :href="src" target="_blank">Full size</a>
    </div>
</template>
<style scoped>
div {
    position: relative;
}
iframe {
    position: absolute;
    top: 0;
    right: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
}
.expandlink {
    position: absolute;
    top: 0;
    right: 0;
}
</style>
<script>
import * as ElementQueries from "css-element-queries";
export default {
    props: ['src', 'width'],
    methods: {
        updateZoom() {
            let origWidth = this.$el.offsetWidth;
            let iframe = this.$el.querySelector('iframe');
            let scaleFactor = origWidth / this.width;
            iframe.style.transform = `scale(${scaleFactor})`;
            iframe.style.transformOrigin = "top right";
            iframe.style.width = `${this.width}px`;
            iframe.style.height = `${100/scaleFactor}%`;
            // console.log('updated zoom', origWidth);
        }
    },
    mounted: function () {
        // let origWidth = this.$el.offsetWidth;
        // let iframe = this.$el.querySelector('iframe');
        // let factor = 2.4;
        // iframe.style.transform = `scale(${1/factor})`;
        // iframe.style.transformOrigin = "top right";
        // iframe.style.width = `${factor * origWidth}px`;
        this.resizeSensor = new ElementQueries.ResizeSensor(this.$el, () => this.updateZoom());
    },
    beforeUnmount: function() {
        this.resizeSensor.detach();
    }
}
</script>