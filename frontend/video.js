import { Blosc, GZip, Zlib, LZ4, Zstd } from 'numcodecs';

async function foo() {

    const codec = new Blosc();
    // or Blosc.fromConfig({ clevel: 5, cname: 'lz4', shuffle: Blosc.SHUFFLE, blocksize: 0 });

    const size = 100000;
    const arr = new Uint32Array(size);
    for (let i = 0; i < size; i++) {
      arr[i] = i;
    }

    const bytes = new Uint8Array(arr.buffer);
    console.log(bytes);
    // Uint8Array(400000) [0, 0, 0, 0,  1, 0, 0, 0,  2, 0, 0, 0, ... ]

    const encoded = await codec.encode(bytes);
    console.log(encoded);
    // Uint8Array(3744) [2, 1, 33, 4, 128, 26, 6, 0, 0, 0, 4, 0, ... ]

    const decoded = await codec.decode(encoded);
    console.log(new Uint32Array(decoded.buffer));
    // Uint32Array(100000) [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,  ... ]

}

window.foo = foo;

import Vue from 'vue';
import common from "./common.js";
import CameraStreamApp from "./CameraStreamApp.vue";

new Vue({
  mixins: [common],
  render: h => h(CameraStreamApp),
}).$mount('#app')

