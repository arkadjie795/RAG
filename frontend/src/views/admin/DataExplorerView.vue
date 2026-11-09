<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <span>🗄️ Publication & Statistical Data Explorer</span>
        </h2>
        <p class="text-xs sm:text-sm text-slate-500 mt-1">
          Jelajahi granular tables hasil ekstraksi BPS Demak di PostgreSQL, inspeksi status integritas nilai statistik, dan verifikasi representasi semantik.
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <span class="text-xs font-bold text-slate-500">Total:</span>
        <span class="px-2.5 py-1 bg-sky-50 text-sky-800 border border-sky-200 rounded-lg text-xs font-black">
          {{ totalTables }} Tabel
        </span>
      </div>
    </div>

    <!-- FILTER TOOLBAR -->
    <div class="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-xs space-y-3">
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <!-- Search Keyword -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Cari Judul / Topik Tabel:</label>
          <div class="relative">
            <input
              v-model="filterSearch"
              @input="debounceFetch"
              type="text"
              placeholder="Contoh: Penduduk, Padi, IPM..."
              class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl pl-8 pr-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </div>
        </div>

        <!-- Filter Kecamatan -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Kecamatan:</label>
          <select
            v-model="filterKecamatan"
            @change="fetchData"
            class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Kecamatan</option>
            <option v-for="kec in KECAMATAN_LIST" :key="kec" :value="kec">{{ kec }}</option>
          </select>
        </div>

        <!-- Filter Tahun -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Tahun Rujukan:</label>
          <select
            v-model="filterTahun"
            @change="fetchData"
            class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Tahun</option>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
            <option value="2021">2021</option>
          </select>
        </div>

        <!-- Filter Kategori -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Kategori:</label>
          <select
            v-model="filterKategori"
            @change="fetchData"
            class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Kategori</option>
            <option value="Kependudukan">Kependudukan</option>
            <option value="Pertanian">Pertanian & Pangan</option>
            <option value="Sosial">Sosial & IPM</option>
            <option value="Ekonomi">Ekonomi & PDRB</option>
            <option value="Perikanan">Perikanan</option>
          </select>
        </div>
      </div>
    </div>

    <!-- DATA TABLE LIST -->
    <div class="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs text-slate-700">
          <thead class="bg-slate-50/80 border-b border-slate-200 text-slate-600 uppercase text-[10px] font-bold tracking-wider">
            <tr>
              <th class="px-4 py-3.5">Judul Tabel Statistik</th>
              <th class="px-4 py-3.5">Wilayah</th>
              <th class="px-4 py-3.5">Tahun</th>
              <th class="px-4 py-3.5">Hal.</th>
              <th class="px-4 py-3.5">Struktur</th>
              <th class="px-4 py-3.5">Satuan</th>
              <th class="px-4 py-3.5 text-right">Aksi</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="isLoading" class="text-center">
              <td colspan="7" class="py-12 text-slate-400">
                <RefreshCw class="w-5 h-5 animate-spin mx-auto mb-2 text-sky-600" />
                <span>Memuat data tabel dari PostgreSQL...</span>
              </td>
            </tr>

            <tr v-else-if="tables.length === 0" class="text-center">
              <td colspan="7" class="py-12 text-slate-400">
                <Database class="w-6 h-6 mx-auto mb-2 text-slate-300" />
                <span>Tidak ada tabel statistik yang cocok dengan filter.</span>
              </td>
            </tr>

            <tr
              v-for="tbl in tables"
              :key="tbl.table_id"
              class="hover:bg-sky-50/40 transition group cursor-pointer"
              @click="openProofOfData(tbl.table_id)"
            >
              <td class="px-4 py-3.5 font-bold text-slate-900 group-hover:text-sky-800 transition">
                {{ tbl.judul_tabel }}
              </td>
              <td class="px-4 py-3.5">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700">
                  {{ tbl.daerah || 'Kabupaten Demak' }}
                </span>
              </td>
              <td class="px-4 py-3.5 font-mono">{{ tbl.tahun || '-' }}</td>
              <td class="px-4 py-3.5 font-mono text-slate-500">{{ tbl.halaman || '-' }}</td>
              <td class="px-4 py-3.5 text-slate-500">
                <span class="font-mono font-bold text-slate-700">{{ tbl.row_count }}</span> baris ×
                <span class="font-mono font-bold text-slate-700">{{ tbl.column_count }}</span> kol
              </td>
              <td class="px-4 py-3.5 text-slate-500 truncate max-w-[120px]">{{ tbl.satuan || '-' }}</td>
              <td class="px-4 py-3.5 text-right">
                <button
                  type="button"
                  @click.stop="openProofOfData(tbl.table_id)"
                  class="px-2.5 py-1.5 rounded-lg text-[11px] font-bold bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 transition cursor-pointer"
                >
                  Proof of Data
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- SLIDE-OVER DRAWER: PROOF OF DATA (DETAIL INSPEKSI SEL POSTGRESQL) -->
    <!-- ================================================================= -->
    <div
      v-if="activeDrawer"
      class="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end transition-opacity"
      @click.self="closeDrawer"
    >
      <div class="w-full max-w-3xl bg-white h-full shadow-2xl flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200">
        <!-- Drawer Header -->
        <div class="p-5 border-b border-slate-200 flex items-start justify-between bg-slate-50">
          <div>
            <div class="flex items-center space-x-2">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                PostgreSQL Proof of Data
              </span>
              <span class="text-xs font-mono text-slate-500">Tabel ID: {{ selectedTableData?.table_id }}</span>
            </div>
            <h3 class="text-base font-extrabold text-slate-900 mt-2">
              {{ selectedTableData?.judul_tabel }}
            </h3>
            <p class="text-xs text-slate-500 mt-0.5">
              Sumber: {{ selectedTableData?.sumber || 'BPS Kabupaten Demak' }} | Hal. {{ selectedTableData?.halaman }}
            </p>
          </div>

          <button
            @click="closeDrawer"
            class="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-200 transition cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Drawer Body -->
        <div class="p-5 space-y-5 flex-1">
          <!-- Loading Detail -->
          <div v-if="isLoadingDetail" class="text-center py-12 text-slate-400">
            <RefreshCw class="w-6 h-6 animate-spin mx-auto mb-2 text-sky-600" />
            <span>Mengambil sel data langsung dari PostgreSQL...</span>
          </div>

          <div v-else-if="selectedTableData" class="space-y-5">
            <!-- 1. Raw Data Matrix -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                  <Grid class="w-4 h-4 text-sky-600" />
                  <span>Matriks Sel Data Mentah (Sanitasi Nilai BPS):</span>
                </h4>
                <span class="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-bold">
                  ✓ Simbol '-' dipertahankan (Status NIL)
                </span>
              </div>

              <div class="border border-slate-200 rounded-xl overflow-x-auto max-h-72">
                <table class="w-full text-xs text-left">
                  <thead class="bg-slate-100/80 border-b border-slate-200 font-bold text-slate-700">
                    <tr>
                      <th
                        v-for="(h, hIdx) in selectedTableData.headers"
                        :key="hIdx"
                        class="px-3 py-2 border-r border-slate-200 last:border-r-0 whitespace-nowrap"
                      >
                        {{ h }}
                      </th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100 font-mono text-[11px]">
                    <tr v-for="(row, rIdx) in selectedTableData.rows" :key="rIdx" class="hover:bg-slate-50">
                      <td
                        v-for="(val, cIdx) in row"
                        :key="cIdx"
                        class="px-3 py-1.5 border-r border-slate-200 last:border-r-0 whitespace-nowrap"
                      >
                        <span v-if="val === '-' || val === null" class="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 font-bold text-[10px]">
                          NIL (-)
                        </span>
                        <span v-else>{{ val }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 2. Natural Language Representation (Fed to LLM) -->
            <div class="space-y-2">
              <h4 class="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                <FileCode class="w-4 h-4 text-sky-600" />
                <span>Representasi Teks Alami (Konteks RAG yang Dikirim ke LLM):</span>
              </h4>
              <div class="bg-slate-900 text-slate-200 p-3.5 rounded-xl text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                {{ selectedTableData.representasi_teks }}
              </div>
            </div>

            <!-- 3. Catatan Footnote & Satuan -->
            <div class="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div>
                <p class="text-slate-400 text-[11px]">Satuan Pengukuran:</p>
                <p class="font-bold text-slate-800">{{ selectedTableData.satuan || 'Tidak dicantumkan' }}</p>
              </div>
              <div>
                <p class="text-slate-400 text-[11px]">Catatan / Footnote:</p>
                <p class="font-bold text-slate-800">{{ selectedTableData.catatan || '-' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Drawer Footer -->
        <div class="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            type="button"
            @click="closeDrawer"
            class="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-bold transition cursor-pointer"
          >
            Tutup Inspeksi
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  Search,
  Database,
  RefreshCw,
  X,
  Grid,
  FileCode
} from 'lucide-vue-next'
import { getStatisticalTables, getTableDetail } from '../../lib/api'

const KECAMATAN_LIST = [
  'Bonang', 'Demak', 'Dempet', 'Gajah', 'Guntur', 'Karanganyar',
  'Karangawen', 'Karangtengah', 'Kebonagung', 'Mijen', 'Mranggen',
  'Sayung', 'Wedung', 'Wonosalam'
]

const tables = ref([])
const totalTables = ref(0)
const isLoading = ref(false)

const filterSearch = ref('')
const filterKecamatan = ref('')
const filterTahun = ref('')
const filterKategori = ref('')

// Drawer State
const activeDrawer = ref(false)
const isLoadingDetail = ref(false)
const selectedTableData = ref(null)

let debounceTimer = null

onMounted(() => {
  fetchData()
})

function debounceFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchData, 400)
}

async function fetchData() {
  isLoading.value = true
  try {
    const params = {
      search: filterSearch.value || undefined,
      kecamatan: filterKecamatan.value || undefined,
      tahun: filterTahun.value || undefined,
      kategori: filterKategori.value || undefined,
      limit: 50
    }
    const res = await getStatisticalTables(params)
    tables.value = res.items || []
    totalTables.value = res.total || 0
  } catch (err) {
    console.error('Error fetching tables:', err)
  } finally {
    isLoading.value = false
  }
}

async function openProofOfData(tableId) {
  activeDrawer.value = true
  isLoadingDetail.value = true
  selectedTableData.value = null
  try {
    const res = await getTableDetail(tableId)
    selectedTableData.value = res.data
  } catch (err) {
    alert(`Gagal memuat detail tabel: ${err.message}`)
  } finally {
    isLoadingDetail.value = false
  }
}

function closeDrawer() {
  activeDrawer.value = false
  selectedTableData.value = null
}
</script>
