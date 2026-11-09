<template>
  <div class="space-y-6 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <span>🧠 Vector & Knowledge Observability</span>
        </h2>
        <p class="text-xs sm:text-sm text-slate-500 mt-1">
          Telemetri indeks pgvector HNSW, efisiensi persistent embedding cache, dan pengujian kualitas pencarian semantik hibrida (RRF).
        </p>
      </div>

      <button
        type="button"
        @click="loadStats"
        class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 self-start sm:self-auto cursor-pointer"
      >
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoadingStats }" />
        <span>Segarkan Telemetri</span>
      </button>
    </div>

    <!-- KPI STATS CARDS -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <p class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Vector Chunks</p>
        <p class="text-2xl font-black text-slate-900 mt-1 font-mono">{{ stats.total_chunks }}</p>
        <p class="text-[11px] text-emerald-600 mt-1 flex items-center space-x-1 font-medium">
          <span>✓ pgvector HNSW terindeks</span>
        </p>
      </div>

      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <p class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Cached Embeddings</p>
        <p class="text-2xl font-black text-sky-700 mt-1 font-mono">{{ stats.cached_embeddings }}</p>
        <p class="text-[11px] text-slate-500 mt-1 font-medium">MD5 Hash-deduplicated</p>
      </div>

      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <p class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Tabel Terindeks</p>
        <p class="text-2xl font-black text-indigo-700 mt-1 font-mono">{{ stats.total_tables }}</p>
        <p class="text-[11px] text-slate-500 mt-1 font-medium">Dari {{ stats.total_publications }} publikasi</p>
      </div>

      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <p class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Metode Pencarian</p>
        <p class="text-lg font-black text-orange-600 mt-1 font-mono">Hybrid RRF</p>
        <p class="text-[11px] text-slate-500 mt-1 font-medium">Dense Vector + FTS Bahasa</p>
      </div>
    </div>

    <!-- SEMANTIC SEARCH PLAYGROUND -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-black text-slate-900 flex items-center space-x-2">
          <Sparkles class="w-4 h-4 text-sky-600" />
          <span>Semantic & Hybrid Search Playground</span>
        </h3>
        <span class="text-xs text-slate-400">Pengujian Live Kueri RRF</span>
      </div>

      <form @submit.prevent="runTestSearch" class="flex flex-col sm:flex-row gap-3">
        <input
          v-model="searchQuery"
          type="text"
          required
          placeholder="Ketik kueri pencarian data statistik (misal: Jumlah penduduk Mranggen 2024)..."
          class="flex-1 text-xs bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
        />

        <select
          v-model="searchKecamatan"
          class="text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
        >
          <option value="">Semua Kecamatan</option>
          <option v-for="kec in KECAMATAN_LIST" :key="kec" :value="kec">{{ kec }}</option>
        </select>

        <button
          type="submit"
          :disabled="isSearching"
          class="px-5 py-2.5 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer disabled:opacity-50"
        >
          <Search class="w-3.5 h-3.5" />
          <span>{{ isSearching ? 'Mencari...' : 'Uji Retrieval' }}</span>
        </button>
      </form>

      <!-- Results Display -->
      <div v-if="searchResults.length > 0" class="space-y-3 pt-2">
        <p class="text-xs font-bold text-slate-700">
          Ditemukan {{ searchResults.length }} Chunks Relevan (Reciprocal Rank Fusion):
        </p>

        <div class="space-y-2.5">
          <div
            v-for="(res, idx) in searchResults"
            :key="idx"
            class="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="font-bold text-sky-800 text-sm">{{ res.judul_tabel || res.dokumen_sumber }}</span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-100 text-sky-800">
                Score: {{ Number(res.score || 0).toFixed(4) }}
              </span>
            </div>

            <p class="text-slate-600 line-clamp-3 font-mono text-[11px] bg-white p-2.5 rounded-lg border border-slate-200">
              {{ res.representasi_teks || res.konten_lengkap }}
            </p>

            <div class="flex items-center space-x-4 text-[11px] text-slate-400">
              <span>Publikasi: <strong>{{ res.dokumen_sumber }}</strong></span>
              <span>Hal: <strong>{{ res.halaman }}</strong></span>
              <span>Tahun: <strong>{{ res.tahun }}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RefreshCw, Sparkles, Search } from 'lucide-vue-next'
import { getVectorStats, runSearchPlayground } from '../../lib/api'

const KECAMATAN_LIST = [
  'Bonang', 'Demak', 'Dempet', 'Gajah', 'Guntur', 'Karanganyar',
  'Karangawen', 'Karangtengah', 'Kebonagung', 'Mijen', 'Mranggen',
  'Sayung', 'Wedung', 'Wonosalam'
]

const stats = ref({
  total_chunks: 0,
  cached_embeddings: 0,
  total_tables: 0,
  total_publications: 0
})
const isLoadingStats = ref(false)

const searchQuery = ref('Jumlah penduduk Kabupaten Demak tahun 2024')
const searchKecamatan = ref('')
const isSearching = ref(false)
const searchResults = ref([])

onMounted(() => {
  loadStats()
})

async function loadStats() {
  isLoadingStats.value = true
  try {
    const res = await getVectorStats()
    stats.value = res
  } catch (err) {
    console.error('Error loading vector stats:', err)
  } finally {
    isLoadingStats.value = false
  }
}

async function runTestSearch() {
  if (!searchQuery.value.trim() || isSearching.value) return
  isSearching.value = true
  searchResults.value = []
  try {
    const res = await runSearchPlayground(
      searchQuery.value.trim(),
      searchKecamatan.value || null,
      null,
      4
    )
    searchResults.value = res.results || []
  } catch (err) {
    alert(`Uji retrieval gagal: ${err.message}`)
  } finally {
    isSearching.value = false
  }
}
</script>
