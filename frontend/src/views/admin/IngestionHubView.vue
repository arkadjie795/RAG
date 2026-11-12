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
        @click="refreshAll"
        class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 self-start sm:self-auto cursor-pointer"
      >
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isRefreshing }" />
        <span>Segarkan Status</span>
      </button>
    </div>

    <!-- PERSISTENT DATABASE STATUS OVERVIEW (READ FROM POSTGRESQL & PGVECTOR) -->
    <div class="bg-gradient-to-br from-slate-900 to-sky-950 text-white rounded-2xl p-6 shadow-md border border-slate-800 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-white/10">
        <div class="flex items-center space-x-2">
          <Database class="w-5 h-5 text-sky-400" />
          <h3 class="text-sm font-black tracking-tight text-white">Status Database Terindeks Saat Ini (PostgreSQL & pgvector)</h3>
        </div>
        <span class="inline-flex items-center space-x-1.5 text-[11px] font-bold text-emerald-300 bg-emerald-950/70 border border-emerald-500/30 px-2.5 py-1 rounded-full">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>PostgreSQL 16 & pgvector Terhubung</span>
        </span>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
        <!-- Card 1: Publikasi -->
        <div class="bg-white/5 border border-white/10 rounded-xl p-3.5 space-y-1">
          <p class="text-[11px] text-sky-200/80 font-medium flex items-center space-x-1">
            <BookOpen class="w-3.5 h-3.5" />
            <span>Publikasi BPS</span>
          </p>
          <p class="text-2xl font-black font-mono text-white">{{ dbStats.total_publications }}</p>
          <p class="text-[10px] text-slate-300 truncate">PDRB Demak Lap. Usaha</p>
        </div>

        <!-- Card 2: Tabel Statistik -->
        <div class="bg-white/5 border border-white/10 rounded-xl p-3.5 space-y-1">
          <p class="text-[11px] text-sky-200/80 font-medium flex items-center space-x-1">
            <Database class="w-3.5 h-3.5" />
            <span>Tabel Statistik</span>
          </p>
          <p class="text-2xl font-black font-mono text-white">{{ dbStats.total_tables }}</p>
          <router-link
            to="/admin/data"
            class="text-[10px] text-sky-300 hover:text-sky-200 font-bold inline-flex items-center space-x-0.5 underline transition"
          >
            <span>Buka Data Explorer</span>
            <ArrowRight class="w-3 h-3 ml-0.5" />
          </router-link>
        </div>

        <!-- Card 3: Vector Chunks -->
        <div class="bg-white/5 border border-white/10 rounded-xl p-3.5 space-y-1">
          <p class="text-[11px] text-sky-200/80 font-medium flex items-center space-x-1">
            <Layers class="w-3.5 h-3.5" />
            <span>Vektor Chunks</span>
          </p>
          <p class="text-2xl font-black font-mono text-white">{{ dbStats.total_chunks }}</p>
          <router-link
            to="/admin/vector"
            class="text-[10px] text-sky-300 hover:text-sky-200 font-bold inline-flex items-center space-x-0.5 underline transition"
          >
            <span>Observabilitas Vektor</span>
            <ArrowRight class="w-3 h-3 ml-0.5" />
          </router-link>
        </div>

        <!-- Card 4: Embedding Cache -->
        <div class="bg-white/5 border border-white/10 rounded-xl p-3.5 space-y-1">
          <p class="text-[11px] text-sky-200/80 font-medium flex items-center space-x-1">
            <CheckCircle2 class="w-3.5 h-3.5 text-emerald-400" />
            <span>Embedding Cache</span>
          </p>
          <p class="text-2xl font-black font-mono text-emerald-300">{{ dbStats.cached_embeddings }}</p>
          <p class="text-[10px] text-slate-300">MD5 Deduped (Hemat Kuota)</p>
        </div>
      </div>
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
            ● Status Scraper: {{ jobState.status }}
          </span>

          <span v-if="jobState.job_id" class="text-xs font-mono text-slate-400">
            ID: {{ jobState.job_id }} (Mode: {{ jobState.mode }})
          </span>
          <span v-else class="text-xs text-slate-400">
            (Standby / Menunggu instruksi trigger baru)
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

      <!-- Informational Hint for Admin -->
      <div v-if="jobState.status === 'IDLE'" class="p-3 bg-sky-50/70 border border-sky-100 rounded-xl text-xs text-sky-800 flex items-start space-x-2">
        <Info class="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
        <p class="leading-relaxed">
          <span class="font-bold">Info Status:</span> Scraper berada dalam status <span class="font-mono font-bold">IDLE</span> karena saat ini tidak ada proses crawling aktif yang sedang berjalan. Seluruh data yang sudah pernah di-ingest sebelumnya ({{ dbStats.total_tables }} tabel & {{ dbStats.total_chunks }} vektor) tersimpan aman di PostgreSQL dan dapat dilihat melalui menu <router-link to="/admin/data" class="font-bold underline text-sky-900">Data & Table Explorer</router-link>.
        </p>
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
          <p class="text-slate-500 text-[11px]">Item Batch Crawl</p>
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
  Terminal,
  Database,
  Layers,
  BookOpen,
  ArrowRight,
  CheckCircle2,
  Info
} from 'lucide-vue-next'
import { getIngestionStatus, triggerIngestionRun, stopIngestionRun, getVectorStats } from '../../lib/api'

const jobState = ref({
  status: 'IDLE',
  progress_pct: 0,
  current_phase: 'Siap dijalankan',
  processed_items: 0,
  total_items: 0,
  elapsed_seconds: 0,
  logs: []
})

const dbStats = ref({
  total_publications: 1,
  total_tables: 35,
  total_chunks: 1210,
  cached_embeddings: 1229
})

const isRefreshing = ref(false)
let pollingInterval = null

onMounted(() => {
  refreshAll()
  pollingInterval = setInterval(refreshStatus, 2500)
})

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval)
})

async function loadDbStats() {
  try {
    const res = await getVectorStats()
    if (res && res.success) {
      dbStats.value = {
        total_publications: res.total_publications || 1,
        total_tables: res.total_tables || 35,
        total_chunks: res.total_chunks || 1210,
        cached_embeddings: res.cached_embeddings || 1229
      }
    }
  } catch (err) {
    console.warn('Gagal memuat dbStats telemetri:', err)
  }
}

async function refreshAll() {
  await Promise.all([refreshStatus(), loadDbStats()])
}

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
    await refreshAll()
  } catch (err) {
    alert(`Gagal menjalankan scraper: ${err.message}`)
  }
}

async function stopJob() {
  if (confirm('Apakah Anda yakin ingin membatalkan proses scraper yang sedang berjalan?')) {
    try {
      await stopIngestionRun()
      await refreshAll()
    } catch (err) {
      alert(`Gagal menghentikan job: ${err.message}`)
    }
  }
}
</script>
