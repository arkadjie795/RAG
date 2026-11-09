<template>
  <div class="space-y-6 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <span>🖥️ System Logs & Telemetry Health</span>
        </h2>
        <p class="text-xs sm:text-sm text-slate-500 mt-1">
          Pemantauan kesehatan runtime backend FastAPI, koneksi PostgreSQL terpusat, dan streaming log real-time.
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <button
          type="button"
          @click="togglePause"
          class="px-3 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer border"
          :class="isPaused
            ? 'bg-amber-50 text-amber-800 border-amber-300'
            : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'"
        >
          <Pause v-if="!isPaused" class="w-3.5 h-3.5 text-slate-600" />
          <Play v-else class="w-3.5 h-3.5 text-amber-700" />
          <span>{{ isPaused ? 'Lanjutkan Stream' : 'Jeda Stream' }}</span>
        </button>

        <button
          type="button"
          @click="fetchLogs"
          class="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isFetching }" />
          <span>Segarkan</span>
        </button>
      </div>
    </div>

    <!-- SERVER HEALTH STATUS CARDS -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-slate-500">PostgreSQL 16 Enterprise</span>
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
        </div>
        <p class="text-base font-extrabold text-slate-900 mt-2 font-mono">10.133.21.24:5433</p>
        <p class="text-[11px] text-slate-500 mt-0.5">Database: <strong class="text-slate-700">bps_rag3321</strong></p>
      </div>

      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-slate-500">pgvector Ekstensi</span>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            v0.8.1 Active
          </span>
        </div>
        <p class="text-base font-extrabold text-slate-900 mt-2 font-mono">HNSW Cosine (&lt;=&gt;)</p>
        <p class="text-[11px] text-slate-500 mt-0.5">Index ef_search: 64</p>
      </div>

      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-slate-500">Model AI Terhubung</span>
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
        </div>
        <p class="text-base font-extrabold text-sky-800 mt-2 font-mono">{{ healthData.llm_provider?.model || 'Gemini 3.5' }}</p>
        <p class="text-[11px] text-slate-500 mt-0.5">Status: <strong class="text-emerald-700">API Key Valid</strong></p>
      </div>
    </div>

    <!-- LOG CONSOLE -->
    <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
      <div class="flex items-center justify-between text-xs">
        <div class="flex items-center space-x-2 font-bold text-slate-700">
          <Terminal class="w-4 h-4 text-slate-500" />
          <span>Live Console Stream (Loguru)</span>
        </div>

        <div class="flex items-center space-x-3 text-[11px] text-slate-500">
          <label class="flex items-center space-x-1.5 cursor-pointer">
            <input type="checkbox" v-model="autoScroll" class="rounded text-sky-600 focus:ring-sky-500" />
            <span>Auto-Scroll</span>
          </label>
          <button @click="logs = []" class="hover:text-red-600 cursor-pointer">Bersihkan Layar</button>
        </div>
      </div>

      <!-- Console Window -->
      <div
        ref="consoleRef"
        class="bg-slate-950 text-slate-200 font-mono text-xs rounded-xl p-4 max-h-[500px] overflow-y-auto space-y-1.5 leading-relaxed"
      >
        <div v-if="logs.length === 0" class="text-slate-500 italic">
          Menghubungkan ke log stream sistem...
        </div>

        <div
          v-for="(line, idx) in logs"
          :key="idx"
          class="break-all"
          :class="{
            'text-emerald-400': line.includes('| INFO'),
            'text-amber-400': line.includes('| WARNING'),
            'text-rose-400': line.includes('| ERROR'),
            'text-sky-300': line.includes('| DEBUG')
          }"
        >
          {{ line }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import {
  RefreshCw,
  Terminal,
  Pause,
  Play
} from 'lucide-vue-next'
import { getSystemHealth, getRecentLogs } from '../../lib/api'

const healthData = ref({})
const logs = ref([])
const isFetching = ref(false)
const isPaused = ref(false)
const autoScroll = ref(true)
const consoleRef = ref(null)

let pollTimer = null

onMounted(async () => {
  await fetchHealth()
  await fetchLogs()
  pollTimer = setInterval(() => {
    if (!isPaused.value) {
      fetchLogs()
    }
  }, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function fetchHealth() {
  try {
    const res = await getSystemHealth()
    healthData.value = res
  } catch (err) {
    console.error('Error fetching health:', err)
  }
}

async function fetchLogs() {
  isFetching.value = true
  try {
    const res = await getRecentLogs(100)
    logs.value = res.logs || []
    if (autoScroll.value) {
      await nextTick()
      if (consoleRef.value) {
        consoleRef.value.scrollTop = consoleRef.value.scrollHeight
      }
    }
  } catch (err) {
    console.error('Error fetching logs:', err)
  } finally {
    isFetching.value = false
  }
}

function togglePause() {
  isPaused.value = !isPaused.value
}
</script>
