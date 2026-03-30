import { createApp } from 'vue';
import FileViewer from '@/pages/FileViewer.vue';

import '@/css/main.scss';

const app = createApp(FileViewer);
app.mount('#viewer-app');
