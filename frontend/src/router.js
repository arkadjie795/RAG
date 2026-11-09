import { createRouter, createWebHistory } from 'vue-router'
import { getAuthToken } from './lib/api'

// Layouts
import PublicLayout from './layouts/PublicLayout.vue'
import AdminLayout from './layouts/AdminLayout.vue'

// Views
import PublicChatView from './views/public/PublicChatView.vue'
import AdminLoginView from './views/admin/AdminLoginView.vue'
import IngestionHubView from './views/admin/IngestionHubView.vue'
import DataExplorerView from './views/admin/DataExplorerView.vue'
import VectorObservabilityView from './views/admin/VectorObservabilityView.vue'
import SystemLogsView from './views/admin/SystemLogsView.vue'

const routes = [
  // ==========================================
  // PUBLIC PORTAL (Sahabat Data Chatbot BPS)
  // ==========================================
  {
    path: '/',
    component: PublicLayout,
    children: [
      {
        path: '',
        name: 'PublicChat',
        component: PublicChatView,
        meta: { title: 'Sahabat Data BPS Demak (3321)' }
      },
      {
        path: 'chat',
        redirect: '/'
      }
    ]
  },

  // ==========================================
  // ADMIN & MONITORING PORTAL (SIPETRA SSO READY)
  // ==========================================
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLoginView,
    meta: { title: 'Login Admin & SSO SIPETRA' }
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/admin/ingestion'
      },
      {
        path: 'ingestion',
        name: 'AdminIngestion',
        component: IngestionHubView,
        meta: { title: 'Data Ingestion & Scraper Hub', requiresAuth: true }
      },
      {
        path: 'data',
        name: 'AdminDataExplorer',
        component: DataExplorerView,
        meta: { title: 'Publication & Data Explorer', requiresAuth: true }
      },
      {
        path: 'vector',
        name: 'AdminVector',
        component: VectorObservabilityView,
        meta: { title: 'Vector Observability & Playground', requiresAuth: true }
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: SystemLogsView,
        meta: { title: 'Realtime System Logs & Health', requiresAuth: true }
      }
    ]
  },

  // Fallback redirect
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guard for Admin Routes
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} | BPS Demak`
  }

  // Check URL query parameters for SSO token handover (?token=bps_...)
  if (to.query && to.query.token) {
    localStorage.setItem('bps_admin_token', to.query.token)
    // Remove token from URL query cleanly
    const cleanedQuery = { ...to.query }
    delete cleanedQuery.token
    return next({ path: to.path, query: cleanedQuery })
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const token = getAuthToken()

  if (requiresAuth && !token) {
    // Redirect to login if unauthenticated
    return next({ path: '/admin/login', query: { redirect: to.fullPath } })
  }

  next()
})

export default router
