import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'

import App from './App.vue'
import router from './router'

let baseURL = ''
if (
 import.meta.env.VITE_ENVIRONMENT == 'dev' ||
 import.meta.env.VITE_ENVIRONMENT == 'test'
) {
 baseURL = 'http://127.0.0.1:5000'
} else {
 //@ts-expect-error
 baseURL = getWebAppBackendUrl('/')
}

// Create axios client for API calls
const axiosClient = axios.create({ baseURL })

// Import and initialize Analysis API
import { AnalysisAPI } from './api/analysisAPI'
export const analysisAPI = new AnalysisAPI(axiosClient)

// Keep legacy ServerAPIFactory for backward compatibility
import { ServerAPIFactory } from './api/serverAPIFactory.ts'
export const serverAPI = new ServerAPIFactory(baseURL)
export default serverAPI

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
