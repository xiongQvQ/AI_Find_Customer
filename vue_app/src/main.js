import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import Home from './views/Home.vue'
import IntelligentSearch from './views/IntelligentSearch.vue'
import CompanySearch from './views/CompanySearch.vue'
import EmployeeSearch from './views/EmployeeSearch.vue'
import SystemSettings from './views/SystemSettings.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/intelligent-search', component: IntelligentSearch },
  { path: '/company-search', component: CompanySearch },
  { path: '/employee-search', component: EmployeeSearch },
  { path: '/settings', component: SystemSettings }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(router)
app.use(createPinia())
app.use(ElementPlus)

app.mount('#app')