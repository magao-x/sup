import { createApp } from 'vue';
import CameraViewer from '@/pages/CameraViewer.vue';

import '@/css/main.scss';

const app = createApp(CameraViewer);
app.mount('#camera-app');
