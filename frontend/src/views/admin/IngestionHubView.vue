<template>
  <div class="space-y-6 max-w-6xl mx-auto">
    <!-- Header Banner -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <span>🚀 Data Ingestion & Scraper Hub</span>
        </h2>
        <p class="text-xs sm:text-sm text-slate-500 mt-1">
          Kontrol eksekusi crawler katalog BPS Demak, ekstraksi tabel PDF (pdfplumber), sanitasi nilai statistik, dan embedding pgvector otomatis.
        </p>
      </div>

      <!-- Action Button -->
      <button
        type="button"
        @click="refreshStatus"
        class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 self-start sm:self-auto cursor-pointer"
      >
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isRefreshing }" />
        <span>Segarkan Status</span>
      </button>
    </div>

    <!-- ACTIVE JOB PROGRESS MONITOR CARD -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <span
            class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border"
            :class="{
              'bg-emerald-50 text-emerald-800 border-emerald-300': jobState.status === 'COMPLETED',
              'bg-sky-50 text-sky-800 border-sky-300 animate-pulse': jobState.status === 'RUNNING',
              'bg-slate-100 text-slate-700 border-slate-300': jobState.status === 'IDLE',
              'bg-red-50 text-red-800 border-red-300': jobState.status === 'FAILED'
            }"
          >
            ● {{ jobState.status }}
          </span>

          <span v-if="jobState.job_id" class="text-xs font-mono text-slate-400">
            ID: {{ jobState.job_id }} (Mode: {{ jobState.mode }})
          </span>
        </div>

        <!-- Stop Button -->
        <button
          v-if="jobState.status === 'RUNNING'"
          @click="stopJob"
          class="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1"
        >
          <Square class="w-3.5 h-3.5" />
          <span>Hentikan Job</span>
        </button>
      </div>

      <!-- Progress Bar -->
      <div class="space-y-2">
        <div class="flex justify-between text-xs font-bold text-slate-700">
          <span>{{ jobState.current_phase || 'Menunggu pemicuan...' }}</span>
          <span>{{ jobState.progress_pct }}%</span>
        </div>
        <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
          <div
            class="bg-gradient-to-r from-sky-600 to-indigo-600 h-full rounded-full transition-all duration-500 ease-out"
            :style="{ width: `${jobState.progress_pct}%` }"
          ></div>
        </div>
      </div>

      <!-- Sub Metrics -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs">
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <p class="text-slate-500 text-[11px]">Item Diproses</p>
          <p class="text-base font-extrabold text-slate-900 mt-0.5">
            {{ jobState.processed_items }} <span class="text-slate-400 font-normal">/ {{ jobState.total_items || '-' }}</span>
          </p>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <p class="text-slate-500 text-[11px]">Waktu Berjalan</p>
          <p class="text-base font-extrabold text-slate-900 mt-0.5">{{ jobState.elapsed_seconds }}s</p>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <p class="text-slate-500 text-[11px]">Integritas Simbol BPS</p>
          <p class="text-base font-extrabold text-emerald-700 mt-0.5">NIL Preserve</p>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <p class="text-slate-500 text-[11px]">Penyimpanan Vektor</p>
          <p class="text-base font-extrabold text-sky-800 mt-0.5">PostgreSQL HNSW</p>
        </div>
      </div>
    </div>

    <!-- TRIGGER OPTIONS GRID -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <!-- Card 1: Statis Mode -->
      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-sky-300 transition">
        <div class="space-y-2">
          <div class="w-10 h-10 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center font-bold">
            <Calendar class="w-5 h-5" />
          </div>
          <h3 class="text-sm font-black text-slate-900">1. Mode Statis (Inkremental)</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Mengecek 2 halaman katalog terbaru portal BPS Demak, mendownload hanya publikasi yang belum pernah di-ingest.
          </p>
        </div>

        <button
          type="button"
          @click="startScraper('statis', 2)"
          :disabled="jobState.status === 'RUNNING'"
          class="w-full py-2.5 px-4 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center justify-center space-x-2 shadow-xs cursor-pointer disabled:opacity-40"
        >
          <Play class="w-3.5 h-3.5" />
          <span>Jalankan Mode Statis</span>
        </button>
      </div>

      <!-- Card 2: Deep Historical Crawl -->
      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-sky-300 transition">
        <div class="space-y-2">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold">
            <Archive class="w-5 h-5" />
          </div>
          <h3 class="text-sm font-black text-slate-900">2. Mode Deep Crawl (All)</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Menelusuri seluruh arsip katalog hingga halaman ke-50 untuk mengindeks seluruh riwayat publikasi Demak.
          </p>
        </div>

        <button
          type="button"
          @click="startScraper('all', 20)"
          :disabled="jobState.status === 'RUNNING'"
          class="w-full py-2.5 px-4 bg-indigo-700 hover:bg-indigo-800 text-white rounded-xl text-xs font-bold transition flex items-center justify-center space-x-2 shadow-xs cursor-pointer disabled:opacity-40"
        >
          <Play class="w-3.5 h-3.5" />
          <span>Jalankan Deep Crawl</span>
        </button>
      </div>

      <!-- Card 3: Single PDF Extraction -->
      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-sky-300 transition">
        <div class="space-y-2">
          <div class="w-10 h-10 rounded-xl bg-orange-50 text-orange-700 flex items-center justify-center font-bold">
            <FileText class="w-5 h-5" />
          </div>
          <h3 class="text-sm font-black text-slate-900">3. Single PDF Mandiri</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Memproses satu dokumen PDF publikasi lokal secara instan tanpa perlu menunggu scraping seluruh katalog web.
          </p>
        </div>

        <button
          type="button"
          @click="startScraper('test', 1)"
          :disabled="jobState.status === 'RUNNING'"
          class="w-full py-2.5 px-4 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-xs font-bold transition flex items-center justify-center space-x-2 shadow-xs cursor-pointer disabled:opacity-40"
        >
          <Play class="w-3.5 h-3.5" />
          <span>Test Single Dokumen</span>
        </button>
      </div>
    </div>

    <!-- JOB LOGS CONSOLE -->
    <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-xs font-bold text-slate-700 flex items-center space-x-2">
          <Terminal class="w-4 h-4 text-slate-500" />
          <span>Telemetri & Log Eksekusi Scraper</span>
        </h3>
        <span class="text-[11px] text-slate-400 font-mono">{{ jobState.logs?.length || 0 }} baris</span>
      </div>

      <div class="bg-slate-900 rounded-xl p-4 font-mono text-xs text-slate-300 max-h-56 overflow-y-auto space-y-1">
        <div v-if="!jobState.logs || jobState.logs.length === 0" class="text-slate-500 italic">
          Belum ada log aktif. Klik salah satu tombol di atas untuk menjalankan crawler.
        </div>
        <div v-for="(log, lIdx) in jobState.logs" :key="lIdx" class="leading-relaxed">
          {{ log }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
  RefreshCw,
  Play,
  Square,
  Calendar,
  Archive,
  FileText,
  Terminal
} from 'lucide-vue-next'
import { getIngestionStatus, triggerIngestionRun, stopIngestionRun } from '../../lib/api'

const jobState = ref({
  status: 'IDLE',
  progress_pct: 0,
  current_phase: 'Siap dijalankan',
  processed_items: 0,
  total_items: 0,
  elapsed_seconds: 0,
  logs: []
})

const isRefreshing = ref(false)
let pollingInterval = null

onMounted(() => {
  refreshStatus()
  pollingInterval = setInterval(refreshStatus, 2500)
})

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval)
})

async function refreshStatus() {
  isRefreshing.value = true
  try {
    const res = await getIngestionStatus()
    jobState.value = res
  } catch (err) {
    console.error('Error fetching job status:', err)
  } finally {
    isRefreshing.value = false
  }
}

async function startScraper(mode, maxPages = 2) {
  try {
    await triggerIngestionRun(mode, maxPages)
    await refreshStatus()
  } catch (err) {
    alert(`Gagal menjalankan scraper: ${err.message}`)
  }
}

async function stopJob() {
  if (confirm('Apakah Anda yakin ingin membatalkan proses scraper yang sedang berjalan?')) {
    try {
      await stopIngestionRun()
      await refreshStatus()
    } catch (err) {
      alert(`Gagal menghentikan job: ${err.message}`)
    }
  }
}
</script>
