<template>
  <div class="min-h-screen flex bg-slate-50 text-slate-800">
    <!-- ========================================== -->
    <!-- SIDEBAR NAV -->
    <!-- ========================================== -->
    <aside class="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 shadow-xs hidden md:flex">
      <div>
        <!-- Sidebar Brand -->
        <div class="h-16 px-5 border-b border-slate-200 flex items-center space-x-3">
          <img
            src="https://upload.wikimedia.org/wikipedia/commons/2/28/Lambang_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg"
            alt="Logo BPS"
            class="h-8 w-auto"
          />
          <div>
            <span class="font-extrabold text-sm text-slate-900 tracking-tight block">RAG3321 Admin</span>
            <span class="text-[10px] font-semibold text-slate-400 block -mt-0.5">BPS Demak Command Center</span>
          </div>
        </div>

        <!-- Navigation Links -->
        <nav class="p-3 space-y-1">
          <router-link
            to="/admin/ingestion"
            class="flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition"
            :class="$route.path.includes('/admin/ingestion')
              ? 'bg-sky-50 text-sky-800 border border-sky-200 font-bold'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
          >
            <DownloadCloud class="w-4 h-4 text-sky-600" />
            <span>Ingestion & Scraper Hub</span>
          </router-link>

          <router-link
            to="/admin/data"
            class="flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition"
            :class="$route.path.includes('/admin/data')
              ? 'bg-sky-50 text-sky-800 border border-sky-200 font-bold'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
          >
            <Database class="w-4 h-4 text-sky-600" />
            <span>Data & Table Explorer</span>
          </router-link>

          <router-link
            to="/admin/vector"
            class="flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition"
            :class="$route.path.includes('/admin/vector')
              ? 'bg-sky-50 text-sky-800 border border-sky-200 font-bold'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
          >
            <Layers class="w-4 h-4 text-sky-600" />
            <span>Vector Observability</span>
          </router-link>

          <router-link
            to="/admin/logs"
            class="flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition"
            :class="$route.path.includes('/admin/logs')
              ? 'bg-sky-50 text-sky-800 border border-sky-200 font-bold'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
          >
            <Activity class="w-4 h-4 text-sky-600" />
            <span>System Logs & Health</span>
          </router-link>
        </nav>
      </div>

      <!-- Bottom Profile / Logout -->
      <div class="p-3 border-t border-slate-200 space-y-2">
        <div class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
          <div class="truncate pr-2">
            <p class="text-xs font-bold text-slate-800 truncate">{{ currentUser?.name || 'Administrator' }}</p>
            <p class="text-[10px] text-slate-500 font-mono truncate">{{ currentUser?.nip || 'Pegawai BPS' }}</p>
          </div>
          <button
            @click="handleLogout"
            class="text-slate-400 hover:text-red-600 p-1 rounded-lg hover:bg-red-50 transition cursor-pointer"
            title="Keluar"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>

        <router-link
          to="/"
          target="_blank"
          class="w-full flex items-center justify-center space-x-1.5 py-2 px-3 text-[11px] font-semibold rounded-lg bg-orange-50 hover:bg-orange-100 text-orange-800 border border-orange-200 transition"
        >
          <span>Buka Portal Publik</span>
          <ExternalLink class="w-3 h-3 ml-1" />
        </router-link>
      </div>
    </aside>

    <!-- ========================================== -->
    <!-- MAIN CONTENT VIEW -->
    <!-- ========================================== -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top Bar -->
      <header class="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
        <!-- Breadcrumb / Section -->
        <div class="flex items-center space-x-2">
          <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">BPS Demak Admin</span>
          <span class="text-slate-300">/</span>
          <span class="text-xs font-extrabold text-slate-900">{{ $route.meta.title }}</span>
        </div>

        <!-- Telemetry Status Pills -->
        <div class="flex items-center space-x-2">
          <!-- PostgreSQL Status Pill -->
          <div class="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span class="font-mono text-[11px]">10.133.21.24 (bps_rag3321)</span>
          </div>

          <!-- Model Tag -->
          <span class="hidden sm:inline-flex px-2.5 py-1 text-[11px] font-bold rounded-full bg-sky-50 text-sky-800 border border-sky-200 font-mono">
            Gemini 3.5
          </span>
        </div>
      </header>

      <!-- View Slot -->
      <main class="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  DownloadCloud,
  Database,
  Layers,
  Activity,
  LogOut,
  ExternalLink
} from 'lucide-vue-next'
import { getCachedUser, checkAuthStatus, logoutAdmin } from '../lib/api'

const router = useRouter()
const currentUser = ref(getCachedUser())

onMounted(async () => {
  try {
    const res = await checkAuthStatus()
    if (res.authenticated) {
      currentUser.value = res.user
    }
  } catch {
    // Ignore error
  }
})

async function handleLogout() {
  await logoutAdmin()
  router.push('/admin/login')
}
</script>
