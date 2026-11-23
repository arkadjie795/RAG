<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <span>🗄️ BPS Demak Official Publications & Tables Catalog</span>
        </h2>
        <p class="text-xs sm:text-sm text-slate-500 mt-1">
          Katalog buku publikasi resmi BPS Kabupaten Demak. Verifikasi berkas fisik PDF, inspeksi metadata rilis, dan buka dropdown untuk menelusuri tabel statistik hasil ekstraksi PostgreSQL.
        </p>
      </div>

      <div class="flex items-center space-x-2 flex-wrap gap-y-2">
        <span class="px-3 py-1.5 bg-sky-50 text-sky-800 border border-sky-200 rounded-xl text-xs font-black flex items-center space-x-1.5">
          <FileText class="w-3.5 h-3.5 text-sky-600" />
          <span>{{ totalPubs }} Publikasi Resmi</span>
        </span>
        <span class="px-3 py-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-black flex items-center space-x-1.5">
          <Database class="w-3.5 h-3.5 text-emerald-600" />
          <span>{{ totalTablesOverall.toLocaleString('id-ID') }} Tabel Terindeks</span>
        </span>
      </div>
    </div>

    <!-- ERROR BANNER: DISCONNECTED DATABASE / VPN REQUIRED -->
    <div
      v-if="errorMessage"
      class="bg-rose-50 border border-rose-200 rounded-2xl p-4 sm:p-5 shadow-xs flex items-start space-x-3.5 animate-in fade-in duration-200"
    >
      <div class="p-2 bg-rose-100 rounded-xl text-rose-700 shrink-0 mt-0.5">
        <AlertCircle class="w-5 h-5 text-rose-600" />
      </div>
      <div class="flex-1 space-y-1.5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h4 class="text-xs font-black text-rose-900 tracking-tight flex items-center space-x-1.5">
            <span>Koneksi ke Basis Data PostgreSQL (10.133.21.24:5433) Terputus</span>
          </h4>
          <button
            type="button"
            @click="fetchData"
            class="px-3 py-1 bg-rose-700 hover:bg-rose-800 text-white rounded-lg text-xs font-bold transition cursor-pointer inline-flex items-center space-x-1.5 shrink-0 self-start sm:self-auto"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoading }" />
            <span>Coba Hubungkan Lagi</span>
          </button>
        </div>
        <p class="text-xs text-rose-800 leading-relaxed">
          Sistem tidak dapat mengambil katalog data dari server BPS Demak (<strong>Timeout / Jaringan Tidak Terjangkau</strong>).
          Ini biasanya terjadi ketika perangkat <strong>belum terhubung ke VPN BPS (FortiClient)</strong> atau berada di luar jaringan intranet kantor BPS Demak.
        </p>
        <div class="text-[11px] font-mono text-rose-700 bg-rose-100/70 px-2.5 py-1.5 rounded-lg border border-rose-200 break-all">
          Detail Error: {{ errorMessage }}
        </div>
        <div class="pt-1 text-[11px] text-slate-600 flex items-center space-x-1">
          <span>💡 <strong>Solusi:</strong> Buka aplikasi <strong>FortiClient</strong> di Windows, klik <strong>Connect</strong> ke VPN BPS, lalu klik tombol "Coba Hubungkan Lagi" di atas.</span>
        </div>
      </div>
    </div>

    <!-- FILTER TOOLBAR -->
    <div class="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-xs space-y-3">
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <!-- Search Keyword -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Cari Judul / ID Publikasi:</label>
          <div class="relative">
            <input
              v-model="filterSearch"
              @input="debounceFetch"
              type="text"
              placeholder="Contoh: Demak Dalam Angka, Sensus, IPM..."
              class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl pl-8 pr-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </div>
        </div>

        <!-- Filter Kecamatan -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Wilayah / Kecamatan:</label>
          <select
            v-model="filterKecamatan"
            @change="fetchData"
            class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Wilayah (Kabupaten & Kecamatan)</option>
            <option value="Kabupaten Demak">Kabupaten Demak (Level Kabupaten)</option>
            <option v-for="kec in KECAMATAN_LIST" :key="kec" :value="kec">{{ kec }}</option>
          </select>
        </div>

        <!-- Filter Tahun -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Tahun Rilis:</label>
          <select
            v-model="filterTahun"
            @change="fetchData"
            class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Tahun</option>
            <option value="2026">2026</option>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
            <option value="2021">2021</option>
            <option value="2020">2020</option>
            <option value="2019">2019</option>
            <option value="2018">2018</option>
          </select>
        </div>

        <!-- Filter Kategori -->
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">Kategori Data:</label>
          <select
            v-model="filterKategori"
            @change="fetchData"
            class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Kategori</option>
            <option value="Statistik Umum">Statistik Umum</option>
            <option value="Sosial">Sosial & IPM</option>
            <option value="Ekonomi">Ekonomi & PDRB</option>
            <option value="Pertanian">Pertanian & Pangan</option>
            <option value="Kependudukan">Kependudukan</option>
          </select>
        </div>
      </div>
    </div>

    <!-- PUBLICATIONS CATALOG TABLE (HIERARCHICAL) -->
    <div class="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs text-slate-700">
          <thead class="bg-slate-50/80 border-b border-slate-200 text-slate-600 uppercase text-[10px] font-bold tracking-wider">
            <tr>
              <th class="w-10 px-3 py-3.5 text-center">#</th>
              <th class="px-4 py-3.5">Judul Buku Publikasi Resmi BPS</th>
              <th class="px-4 py-3.5">Wilayah</th>
              <th class="px-4 py-3.5">Rilis / Tahun</th>
              <th class="px-4 py-3.5">Jml Tabel</th>
              <th class="px-4 py-3.5">Status Berkas</th>
              <th class="px-4 py-3.5 text-right">Aksi & Dropdown</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <!-- Loading Row -->
            <tr v-if="isLoading" class="text-center">
              <td colspan="7" class="py-14 text-slate-400">
                <RefreshCw class="w-6 h-6 animate-spin mx-auto mb-2 text-sky-600" />
                <span class="font-medium text-xs">Memuat katalog publikasi BPS dari PostgreSQL...</span>
              </td>
            </tr>

            <!-- Empty Row -->
            <tr v-else-if="publications.length === 0" class="text-center">
              <td colspan="7" class="py-14 text-slate-400">
                <template v-if="errorMessage">
                  <AlertCircle class="w-8 h-8 mx-auto mb-2 text-rose-400" />
                  <span class="font-bold text-xs text-rose-700 block">Koneksi ke Basis Data PostgreSQL Terputus</span>
                  <span class="text-[11px] text-slate-500 mt-1 block max-w-md mx-auto">
                    Katalog publikasi tidak dapat dimuat karena server basis data di 10.133.21.24 tidak merespons. Silakan hubungkan kembali VPN BPS (FortiClient) lalu klik "Coba Hubungkan Lagi".
                  </span>
                </template>
                <template v-else>
                  <Database class="w-7 h-7 mx-auto mb-2 text-slate-300" />
                  <span class="font-medium text-xs">Tidak ada publikasi BPS yang cocok dengan kriteria filter.</span>
                </template>
              </td>
            </tr>

            <!-- Publication Rows -->
            <template v-else v-for="pub in publications" :key="pub.doc_id">
              <!-- Main Publication Item Row -->
              <tr
                class="hover:bg-sky-50/30 transition group cursor-pointer"
                :class="{ 'bg-sky-50/50': expandedPubIds.has(pub.doc_id) }"
                @click="togglePublication(pub.doc_id)"
              >
                <!-- Expand Chevron Toggle -->
                <td class="px-3 py-3.5 text-center" @click.stop="togglePublication(pub.doc_id)">
                  <button
                    type="button"
                    class="p-1 rounded hover:bg-slate-200 text-slate-400 group-hover:text-sky-700 transition cursor-pointer"
                    :title="expandedPubIds.has(pub.doc_id) ? 'Tutup daftar tabel' : 'Buka daftar tabel'"
                  >
                    <ChevronDown v-if="expandedPubIds.has(pub.doc_id)" class="w-4 h-4 text-sky-700" />
                    <ChevronRight v-else class="w-4 h-4" />
                  </button>
                </td>

                <!-- Judul Buku Publikasi & ID -->
                <td class="px-4 py-3.5 font-bold text-slate-900 group-hover:text-sky-900 transition">
                  <div class="flex items-center space-x-2">
                    <span class="text-xs font-bold leading-snug">{{ pub.judul }}</span>
                  </div>
                  <div class="flex items-center space-x-2 mt-1">
                    <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200">
                      ID: {{ pub.doc_id }}
                    </span>
                    <span v-if="pub.kategori" class="text-[10px] text-slate-400 font-medium">
                      • {{ pub.kategori }}
                    </span>
                  </div>
                </td>

                <!-- Wilayah Badge -->
                <td class="px-4 py-3.5 whitespace-nowrap">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-semibold border"
                    :class="pub.daerah.includes('Kecamatan') 
                      ? 'bg-indigo-50 text-indigo-700 border-indigo-200' 
                      : 'bg-slate-100 text-slate-700 border-slate-200'"
                  >
                    {{ pub.daerah }}
                  </span>
                </td>

                <!-- Tahun / Release Date -->
                <td class="px-4 py-3.5 font-mono text-slate-600 whitespace-nowrap">
                  {{ pub.tahun || '-' }}
                </td>

                <!-- Jml Tabel Badge -->
                <td class="px-4 py-3.5 whitespace-nowrap">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-bold border"
                    :class="pub.total_tabel > 0 
                      ? 'bg-sky-50 text-sky-700 border-sky-200' 
                      : 'bg-amber-50 text-amber-700 border-amber-200'"
                  >
                    {{ pub.total_tabel }} Tabel
                  </span>
                </td>

                <!-- Berkas PDF Status -->
                <td class="px-4 py-3.5 whitespace-nowrap">
                  <span
                    v-if="pub.file_path"
                    class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"
                    :title="pub.file_path"
                  >
                    <FileCheck class="w-3 h-3 text-emerald-600" />
                    <span>PDF Tersedia ({{ formatBytes(pub.file_size_bytes) }})</span>
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-500 border border-slate-200"
                  >
                    <span>Belum Diunduh</span>
                  </span>
                </td>

                <!-- Action Buttons -->
                <td class="px-4 py-3.5 text-right whitespace-nowrap" @click.stop>
                  <div class="flex items-center justify-end space-x-2">
                    <button
                      type="button"
                      @click="openVerifyModal(pub.doc_id)"
                      class="px-2.5 py-1.5 rounded-lg text-[11px] font-bold bg-white hover:bg-sky-50 text-sky-700 border border-sky-300 shadow-2xs hover:border-sky-400 transition cursor-pointer flex items-center space-x-1"
                      title="Periksa dan verifikasi integritas berkas PDF publikasi"
                    >
                      <FileCheck class="w-3.5 h-3.5 text-sky-600" />
                      <span>Cek Dokumen</span>
                    </button>

                    <button
                      type="button"
                      @click="togglePublication(pub.doc_id)"
                      class="px-2.5 py-1.5 rounded-lg text-[11px] font-bold transition cursor-pointer flex items-center space-x-1"
                      :class="expandedPubIds.has(pub.doc_id)
                        ? 'bg-sky-700 text-white shadow-2xs'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200'"
                    >
                      <span>{{ expandedPubIds.has(pub.doc_id) ? 'Tutup Tabel' : `Tabel (${pub.total_tabel})` }}</span>
                      <ChevronDown v-if="expandedPubIds.has(pub.doc_id)" class="w-3.5 h-3.5" />
                      <ChevronRight v-else class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </tr>

              <!-- EXPANDED ACCORDION ROW: LIST OF TABLES IN THIS PUBLICATION -->
              <tr v-if="expandedPubIds.has(pub.doc_id)" class="bg-slate-50/60 border-b border-sky-200">
                <td colspan="7" class="p-0">
                  <div class="py-4 px-6 sm:px-10 bg-gradient-to-b from-sky-50/50 to-slate-50/90 border-y border-sky-100">
                    <div class="flex items-center justify-between mb-3">
                      <div class="flex items-center space-x-2">
                        <span class="text-xs font-black text-slate-800 uppercase tracking-wider flex items-center space-x-1.5">
                          <Grid class="w-3.5 h-3.5 text-sky-700" />
                          <span>Daftar Tabel Statistik: {{ pub.judul }}</span>
                        </span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-200">
                          {{ (pubTablesCache[pub.doc_id] || []).length }} Tabel Valid
                        </span>
                        <button
                          type="button"
                          @click.stop="refreshPublicationTables(pub.doc_id)"
                          class="p-1 rounded text-slate-400 hover:text-sky-700 hover:bg-sky-100 transition cursor-pointer"
                          title="Muat ulang tabel publikasi"
                        >
                          <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': isLoadingTables[pub.doc_id] }" />
                        </button>
                      </div>
                      <span class="text-[11px] text-slate-400">
                        Klik <strong>"Proof of Data"</strong> untuk inspeksi sel mentah & representasi semantik LLM.
                      </span>
                    </div>

                    <!-- Loading State for Tables -->
                    <div v-if="isLoadingTables[pub.doc_id]" class="py-8 text-center text-slate-400">
                      <RefreshCw class="w-5 h-5 animate-spin mx-auto mb-1.5 text-sky-600" />
                      <span class="text-xs font-medium">Mengambil data tabel dari PostgreSQL...</span>
                    </div>

                    <!-- Empty Tables State -->
                    <div
                      v-else-if="!pubTablesCache[pub.doc_id] || pubTablesCache[pub.doc_id].length === 0"
                      class="py-6 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl bg-white"
                    >
                      <Database class="w-5 h-5 mx-auto mb-1 text-slate-300" />
                      <span class="text-xs">Tidak ada tabel statistik yang diekstrak dari publikasi ini.</span>
                    </div>

                    <!-- Tables List -->
                    <div v-else class="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-2xs">
                      <table class="w-full text-left text-xs">
                        <thead class="bg-slate-100/90 border-b border-slate-200 text-slate-600 uppercase text-[9px] font-bold tracking-wider">
                          <tr>
                            <th class="w-8 px-3 py-2 text-center">No.</th>
                            <th class="px-3 py-2">Judul Tabel Statistik</th>
                            <th class="px-3 py-2 text-center">Hal.</th>
                            <th class="px-3 py-2">Dimensi</th>
                            <th class="px-3 py-2">Satuan</th>
                            <th class="px-3 py-2">Sumber</th>
                            <th class="px-3 py-2 text-right">Aksi</th>
                          </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 text-[11px]">
                          <tr
                            v-for="(tbl, tIdx) in pubTablesCache[pub.doc_id]"
                            :key="tbl.table_id"
                            class="hover:bg-sky-50/40 transition group cursor-pointer"
                            @click="openProofOfData(tbl.table_id)"
                          >
                            <td class="px-3 py-2 text-center font-mono text-slate-400">{{ tIdx + 1 }}</td>
                            <td class="px-3 py-2 font-bold text-slate-900 group-hover:text-sky-800 transition">
                              <div>{{ tbl.judul_tabel }}</div>
                              <span class="text-[9px] font-mono text-slate-400">ID: {{ tbl.table_id }}</span>
                            </td>
                            <td class="px-3 py-2 text-center font-mono font-bold text-slate-600">
                              <span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">p.{{ tbl.halaman }}</span>
                            </td>
                            <td class="px-3 py-2 text-slate-600 font-mono">
                              <span class="font-bold text-slate-800">{{ tbl.row_count }}</span> b × 
                              <span class="font-bold text-slate-800">{{ tbl.column_count }}</span> k
                            </td>
                            <td class="px-3 py-2 text-slate-500 truncate max-w-[120px]">{{ tbl.satuan || '-' }}</td>
                            <td class="px-3 py-2 text-slate-500 truncate max-w-[130px]">{{ tbl.sumber || 'BPS Kabupaten Demak' }}</td>
                            <td class="px-3 py-2 text-right whitespace-nowrap">
                              <button
                                type="button"
                                @click.stop="openProofOfData(tbl.table_id)"
                                class="px-2 py-1 rounded text-[10px] font-bold bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 transition cursor-pointer"
                              >
                                Proof of Data
                              </button>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Pagination Toolbar -->
      <div class="px-5 py-4 border-t border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="text-xs text-slate-500">
          Menampilkan <span class="font-bold text-slate-800">{{ (currentPage - 1) * pageSize + 1 }}</span>
          hingga <span class="font-bold text-slate-800">{{ Math.min(currentPage * pageSize, totalPubs) }}</span>
          dari <span class="font-bold text-slate-800">{{ totalPubs }}</span> publikasi resmi
        </div>

        <div class="flex items-center space-x-2">
          <button
            type="button"
            @click="prevPage"
            :disabled="currentPage === 1"
            class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer"
          >
            ← Sebelumnya
          </button>
          <span class="text-xs font-mono font-bold text-slate-600 px-2">
            Hal {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            type="button"
            @click="nextPage"
            :disabled="currentPage >= totalPages"
            class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer"
          >
            Berikutnya →
          </button>
        </div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- MODAL: CEK DOKUMEN / VERIFIKASI BERKAS PUBLIKASI RESMI BPS       -->
    <!-- ================================================================= -->
    <div
      v-if="activeVerifyModal"
      class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 transition-opacity animate-in fade-in duration-150"
      @click.self="closeVerifyModal"
    >
      <div class="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col animate-in zoom-in-95 duration-150">
        <!-- Modal Header -->
        <div class="p-5 border-b border-slate-200 flex items-start justify-between bg-gradient-to-r from-sky-50 via-white to-slate-50">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700">
              <FileCheck class="w-5 h-5" />
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Verifikasi Berkas Resmi BPS
                </span>
                <span class="text-[11px] font-mono text-slate-500">ID: {{ verifyData?.doc_id }}</span>
              </div>
              <h3 class="text-sm sm:text-base font-black text-slate-900 mt-1">
                {{ verifyData?.title || 'Memeriksa Dokumen...' }}
              </h3>
            </div>
          </div>

          <button
            @click="closeVerifyModal"
            class="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-200 transition cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-5 sm:p-6 space-y-5 overflow-y-auto max-h-[75vh]">
          <!-- Loading State -->
          <div v-if="isVerifying" class="py-12 text-center text-slate-400">
            <RefreshCw class="w-6 h-6 animate-spin mx-auto mb-2 text-sky-600" />
            <span class="text-xs font-medium">Melakukan verifikasi integritas checksum SHA-256 berkas fisik di server...</span>
          </div>

          <!-- Content Verified -->
          <div v-else-if="verifyData" class="space-y-4">
            <!-- 1. Status Banner -->
            <div
              class="p-4 rounded-xl border flex items-center space-x-3"
              :class="verifyData.file_exists
                ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                : 'bg-amber-50/70 border-amber-200 text-amber-900'"
            >
              <CheckCircle2 v-if="verifyData.file_exists" class="w-5 h-5 text-emerald-600 shrink-0" />
              <AlertCircle v-else class="w-5 h-5 text-amber-600 shrink-0" />
              <div>
                <p class="text-xs font-bold">
                  {{ verifyData.file_exists ? 'Berkas Fisik Terverifikasi Ada di Server' : 'Berkas Fisik Belum Ditemukan di Storage' }}
                </p>
                <p class="text-[11px] text-slate-600 mt-0.5">
                  {{ verifyData.file_exists 
                    ? `Berkas PDF resmi tersimpan valid di penyimpanan lokal server dan siap diproses.`
                    : `Sistem mencatat metadata namun berkas PDF fisik belum berada di direktori lokal.` }}
                </p>
              </div>
            </div>

            <!-- 2. Detail Spesifikasi Berkas -->
            <div class="border border-slate-200 rounded-xl overflow-hidden bg-slate-50/40">
              <div class="bg-slate-100/70 px-4 py-2 border-b border-slate-200">
                <span class="text-[11px] font-bold text-slate-700 uppercase tracking-wider">Spesifikasi & Integritas Dokumen</span>
              </div>
              <div class="p-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <span class="text-slate-400 text-[11px]">Tanggal Rilis BPS:</span>
                  <p class="font-bold text-slate-800">{{ verifyData.release_date }}</p>
                </div>
                <div>
                  <span class="text-slate-400 text-[11px]">Cakupan Wilayah:</span>
                  <p class="font-bold text-slate-800">{{ verifyData.daerah }}</p>
                </div>
                <div>
                  <span class="text-slate-400 text-[11px]">Kategori Publikasi:</span>
                  <p class="font-bold text-slate-800">{{ verifyData.category }}</p>
                </div>
                <div>
                  <span class="text-slate-400 text-[11px]">Jumlah Halaman PDF:</span>
                  <p class="font-bold text-slate-800">{{ verifyData.page_count ? `${verifyData.page_count} Halaman` : 'Tidak terdeteksi' }}</p>
                </div>
                <div>
                  <span class="text-slate-400 text-[11px]">Ukuran Berkas:</span>
                  <p class="font-bold text-slate-800">{{ verifyData.file_size_formatted }} ({{ verifyData.file_size_bytes.toLocaleString('id-ID') }} bytes)</p>
                </div>
                <div>
                  <span class="text-slate-400 text-[11px]">Status Ekstraksi:</span>
                  <span class="inline-block px-2 py-0.5 rounded text-[10px] font-black uppercase bg-sky-100 text-sky-800">
                    {{ verifyData.extraction_status }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 3. Checksum SHA-256 -->
            <div class="space-y-1.5">
              <label class="block text-[11px] font-bold text-slate-700">Checksum Integritas SHA-256 (Anti-Tampering):</label>
              <div class="flex items-center space-x-2">
                <div class="bg-slate-900 text-emerald-400 p-2.5 rounded-xl font-mono text-[11px] flex-1 break-all select-all border border-slate-800">
                  {{ verifyData.checksum_sha256 || 'Checksum belum dihitung' }}
                </div>
                <button
                  type="button"
                  @click="copyChecksum(verifyData.checksum_sha256)"
                  class="px-3 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1"
                  title="Salin Checksum SHA-256"
                >
                  <Check v-if="copiedChecksum" class="w-4 h-4 text-emerald-600" />
                  <Copy v-else class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- 4. Jalur Penyimpanan Lokal (Local File Path) -->
            <div class="space-y-1.5">
              <label class="block text-[11px] font-bold text-slate-700">Jalur File di Server (Local Storage Path):</label>
              <div class="bg-slate-100 text-slate-700 p-2.5 rounded-xl font-mono text-[11px] break-all border border-slate-200">
                {{ verifyData.local_file_path || 'Tidak ada jalur berkas lokal' }}
              </div>
            </div>

            <!-- 5. PostgreSQL Ingestion Metrics -->
            <div class="grid grid-cols-2 gap-3 text-xs">
              <div class="bg-sky-50 border border-sky-200 p-3 rounded-xl text-center">
                <span class="text-[10px] font-bold text-sky-600 uppercase tracking-wider">Tabel Statistik PostgreSQL</span>
                <p class="text-xl font-black text-sky-900 mt-0.5">{{ verifyData.total_tables }} Tabel</p>
                <span class="text-[10px] text-sky-700">Tersimpan di tabel `statistical_tables`</span>
              </div>
              <div class="bg-indigo-50 border border-indigo-200 p-3 rounded-xl text-center">
                <span class="text-[10px] font-bold text-indigo-600 uppercase tracking-wider">Vektor Terindeks pgvector</span>
                <p class="text-xl font-black text-indigo-900 mt-0.5">{{ verifyData.total_chunks }} Chunks</p>
                <span class="text-[10px] text-indigo-700">Tersimpan di tabel `vector_chunks`</span>
              </div>
            </div>

            <!-- 6. Original Web URL -->
            <div v-if="verifyData.pdf_url" class="pt-1 flex items-center justify-between text-xs text-slate-500">
              <span>Sumber Portal Web BPS:</span>
              <a
                :href="verifyData.pdf_url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-sky-600 hover:text-sky-800 font-bold flex items-center space-x-1"
              >
                <span>Buka Tautan Asli BPS</span>
                <ExternalLink class="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            type="button"
            @click="closeVerifyModal"
            class="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-bold transition cursor-pointer"
          >
            Tutup Verifikasi
          </button>
        </div>
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
import { ref, computed, onMounted } from 'vue'
import {
  Search,
  Database,
  RefreshCw,
  X,
  Grid,
  FileCode,
  ChevronRight,
  ChevronDown,
  FileCheck,
  FileText,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Copy,
  Check
} from 'lucide-vue-next'
import {
  getPublications,
  getPublicationTables,
  verifyPublication,
  getTableDetail
} from '../../lib/api'

const KECAMATAN_LIST = [
  'Bonang', 'Demak', 'Dempet', 'Gajah', 'Guntur', 'Karanganyar',
  'Karangawen', 'Karangtengah', 'Kebonagung', 'Mijen', 'Mranggen',
  'Sayung', 'Wedung', 'Wonosalam'
]

// Primary Catalog State
const publications = ref([])
const totalPubs = ref(0)
const totalTablesOverall = ref(0)
const isLoading = ref(false)
const errorMessage = ref('')

// Pagination State
const currentPage = ref(1)
const pageSize = ref(25)
const totalPages = computed(() => Math.ceil(totalPubs.value / pageSize.value) || 1)

// Filters State
const filterSearch = ref('')
const filterKecamatan = ref('')
const filterTahun = ref('')
const filterKategori = ref('')

// Dropdown Accordion State (Hierarchical)
const expandedPubIds = ref(new Set())
const pubTablesCache = ref({})
const isLoadingTables = ref({})

// Document Verification Modal State
const activeVerifyModal = ref(false)
const isVerifying = ref(false)
const verifyData = ref(null)
const copiedChecksum = ref(false)

// Proof of Data Drawer State
const activeDrawer = ref(false)
const isLoadingDetail = ref(false)
const selectedTableData = ref(null)

let debounceTimer = null

onMounted(() => {
  fetchData()
})

function debounceFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchData()
  }, 400)
}

async function fetchData() {
  isLoading.value = true
  errorMessage.value = ''
  pubTablesCache.value = {}
  try {
    const params = {
      search: filterSearch.value || undefined,
      kecamatan: filterKecamatan.value || undefined,
      tahun: filterTahun.value || undefined,
      kategori: filterKategori.value || undefined,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }
    const res = await getPublications(params)
    if (res.success === false || res.error) {
      errorMessage.value = res.error || 'Gagal memuat data dari database PostgreSQL.'
      publications.value = []
      totalPubs.value = 0
    } else {
      publications.value = res.items || []
      totalPubs.value = res.total || 0
      if (res.total_tables_overall !== undefined) {
        totalTablesOverall.value = res.total_tables_overall
      }
    }
  } catch (err) {
    console.error('Error fetching publications:', err)
    errorMessage.value = err.message || 'Koneksi ke backend server gagal.'
    publications.value = []
    totalPubs.value = 0
  } finally {
    isLoading.value = false
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    fetchData()
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    fetchData()
  }
}

async function togglePublication(docId) {
  if (expandedPubIds.value.has(docId)) {
    expandedPubIds.value.delete(docId)
  } else {
    expandedPubIds.value.add(docId)
    // Fetch tables if not cached
    if (!pubTablesCache.value[docId]) {
      await refreshPublicationTables(docId)
    }
  }
}

async function refreshPublicationTables(docId) {
  isLoadingTables.value[docId] = true
  try {
    const res = await getPublicationTables(docId)
    pubTablesCache.value[docId] = res.items || []
  } catch (err) {
    console.error(`Error fetching tables for publication ${docId}:`, err)
    pubTablesCache.value[docId] = []
  } finally {
    isLoadingTables.value[docId] = false
  }
}

async function openVerifyModal(docId) {
  activeVerifyModal.value = true
  isVerifying.value = true
  verifyData.value = null
  copiedChecksum.value = false
  try {
    const res = await verifyPublication(docId)
    verifyData.value = res.data
  } catch (err) {
    alert(`Gagal memverifikasi dokumen publikasi: ${err.message}`)
    activeVerifyModal.value = false
  } finally {
    isVerifying.value = false
  }
}

function closeVerifyModal() {
  activeVerifyModal.value = false
  verifyData.value = null
  copiedChecksum.value = false
}

function copyChecksum(text) {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    copiedChecksum.value = true
    setTimeout(() => {
      copiedChecksum.value = false
    }, 2000)
  })
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

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}
</script>
