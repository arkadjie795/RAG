<template>
  <div class="flex-1 flex flex-col max-w-5xl w-full mx-auto p-4 sm:p-6 lg:p-8">
    <!-- TOP STATS / BANNER -->
    <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs mb-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
            <span>📊 Sahabat Data BPS Kabupaten Demak</span>
          </h1>
          <p class="text-xs sm:text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
            Ajukan pertanyaan seputar indikator statistik resmi (Kependudukan, Pertanian, IPM, Kemiskinan, PDRB) Kabupaten Demak.
          </p>
        </div>

        <!-- Filter Controls -->
        <div class="flex flex-wrap items-center gap-2">
          <select
            v-model="selectedKecamatan"
            class="text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Kecamatan (Otomatis)</option>
            <option v-for="kec in KECAMATAN_LIST" :key="kec" :value="kec">{{ kec }}</option>
          </select>

          <select
            v-model="selectedTahun"
            class="text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Semua Tahun</option>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
          </select>

          <button
            type="button"
            @click="clearChat"
            class="text-xs px-3 py-2 text-slate-600 hover:text-red-700 hover:bg-red-50 border border-slate-300 rounded-xl transition flex items-center space-x-1 cursor-pointer"
            title="Bersihkan riwayat percakapan"
          >
            <Trash2 class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Reset</span>
          </button>
        </div>
      </div>
    </div>

    <!-- CHAT MESSAGES CONTAINER -->
    <div class="flex-1 bg-white border border-slate-200 rounded-2xl p-4 sm:p-6 shadow-xs flex flex-col justify-between min-h-[480px]">
      <div class="space-y-5 overflow-y-auto max-h-[550px] pr-2">
        <!-- Empty State with Quick Prompts -->
        <div v-if="messages.length === 0" class="text-center py-10 space-y-4">
          <div class="w-16 h-16 mx-auto bg-sky-50 rounded-2xl flex items-center justify-center text-sky-700 shadow-inner">
            <MessageSquareText class="w-8 h-8" />
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-800">Mulai Percakapan dengan Sahabat Data</h3>
            <p class="text-xs text-slate-500 max-w-md mx-auto mt-1">
              Pilih pertanyaan contoh di bawah ini atau ketik pertanyaan langsung di kolom chat:
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-2xl mx-auto pt-2">
            <button
              v-for="(prompt, idx) in QUICK_PROMPTS"
              :key="idx"
              @click="submitPrompt(prompt)"
              class="text-left p-3 rounded-xl border border-slate-200 hover:border-sky-300 hover:bg-sky-50/50 text-xs font-medium text-slate-700 transition cursor-pointer flex items-center space-x-2"
            >
              <span class="text-sky-600 font-bold shrink-0">💬</span>
              <span>{{ prompt }}</span>
            </button>
          </div>
        </div>

        <!-- Render Messages -->
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="flex items-start space-x-3"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <!-- Assistant Avatar -->
          <div
            v-if="msg.role === 'assistant'"
            class="w-8 h-8 rounded-xl bg-sky-700 text-white flex items-center justify-center font-black text-xs shrink-0 shadow-xs"
          >
            BPS
          </div>

          <!-- Message Body -->
          <div
            class="max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed"
            :class="msg.role === 'user'
              ? 'bg-slate-900 text-white rounded-br-xs'
              : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-xs'"
          >
            <!-- Formatted Content -->
            <div class="whitespace-pre-wrap">{{ msg.content }}</div>

            <!-- Citations Accordion (Assistant only) -->
            <div v-if="msg.citations && msg.citations.length > 0" class="mt-3 pt-3 border-t border-slate-200/80">
              <span class="text-[11px] font-bold text-slate-500 flex items-center space-x-1 mb-2">
                <BookOpen class="w-3.5 h-3.5 text-sky-600" />
                <span>{{ msg.citations.length }} Sumber Referensi Publikasi BPS:</span>
              </span>

              <div class="space-y-1.5">
                <div
                  v-for="(cit, cIdx) in msg.citations"
                  :key="cIdx"
                  class="bg-white border border-slate-200 p-2.5 rounded-lg text-xs hover:border-sky-300 transition"
                >
                  <p class="font-bold text-sky-800">
                    {{ cit.dokumen_sumber || cit.dokumen || 'Publikasi BPS Kabupaten Demak' }}
                    <span v-if="cit.tahun" class="font-normal text-slate-500">({{ cit.tahun }})</span>
                  </p>
                  <div class="flex items-center space-x-3 text-[11px] text-slate-500 mt-1">
                    <span v-if="cit.halaman">Hal: <strong>{{ cit.halaman }}</strong></span>
                    <span v-if="cit.judul_tabel" class="truncate">Tabel: <strong>{{ cit.judul_tabel }}</strong></span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- User Avatar -->
          <div
            v-if="msg.role === 'user'"
            class="w-8 h-8 rounded-xl bg-orange-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs"
          >
            You
          </div>
        </div>

        <!-- Loading Indicator -->
        <div v-if="isLoading" class="flex items-start space-x-3">
          <div class="w-8 h-8 rounded-xl bg-sky-700 text-white flex items-center justify-center font-bold text-xs shrink-0">
            BPS
          </div>
          <div class="bg-slate-50 border border-slate-200 rounded-2xl rounded-bl-xs p-3.5 flex items-center space-x-2 text-xs text-slate-500">
            <span class="flex h-2 w-2 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-sky-500"></span>
            </span>
            <span>Mencari data resmi di database BPS Demak...</span>
          </div>
        </div>
      </div>

      <!-- INPUT BAR -->
      <div class="pt-4 mt-4 border-t border-slate-100">
        <form @submit.prevent="sendMessage" class="flex items-center space-x-2">
          <input
            v-model="inputQuery"
            type="text"
            placeholder="Ketik pertanyaan data statistik Demak di sini..."
            :disabled="isLoading"
            class="flex-1 text-xs sm:text-sm bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white text-slate-900 transition disabled:opacity-50"
          />

          <button
            type="submit"
            :disabled="!inputQuery.trim() || isLoading"
            class="px-5 py-3 bg-sky-700 hover:bg-sky-800 text-white font-bold rounded-xl text-xs sm:text-sm transition flex items-center space-x-1.5 shadow-xs disabled:opacity-40 cursor-pointer"
          >
            <Send class="w-4 h-4" />
            <span class="hidden sm:inline">Kirim</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import {
  MessageSquareText,
  Send,
  Trash2,
  BookOpen
} from 'lucide-vue-next'
import { sendPublicChatMessage } from '../../lib/api'

const KECAMATAN_LIST = [
  'Bonang', 'Demak', 'Dempet', 'Gajah', 'Guntur', 'Karanganyar',
  'Karangawen', 'Karangtengah', 'Kebonagung', 'Mijen', 'Mranggen',
  'Sayung', 'Wedung', 'Wonosalam'
]

const QUICK_PROMPTS = [
  'Berapa jumlah penduduk Kabupaten Demak tahun 2024?',
  'Bagaimana capaian Indeks Pembangunan Manusia (IPM) Demak?',
  'Berapa produksi padi sawah di Kecamatan Dempet?',
  'Siapa nama Kepala BPS Kabupaten Demak saat ini?'
]

const messages = ref([])
const inputQuery = ref('')
const isLoading = ref(false)
const selectedKecamatan = ref('')
const selectedTahun = ref('')

function submitPrompt(promptText) {
  inputQuery.value = promptText
  sendMessage()
}

async function sendMessage() {
  const query = inputQuery.value.trim()
  if (!query || isLoading.value) return

  // Add user message
  messages.value.push({ role: 'user', content: query })
  inputQuery.value = ''
  isLoading.value = true

  try {
    const payload = {
      message: query,
      session_id: 'public_web_session',
      daerah: selectedKecamatan.value || null,
      tahun: selectedTahun.value || null,
      top_k: 4
    }
    const res = await sendPublicChatMessage(payload)
    const assistantData = res.data || {}

    messages.value.push({
      role: 'assistant',
      content: assistantData.answer || 'Tidak ada respons yang dapat ditampilkan.',
      citations: assistantData.citations || []
    })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `Terjadi kendala saat menghubungi server data: ${error.message}. Silakan coba lagi.`,
      citations: []
    })
  } finally {
    isLoading.value = false
  }
}

function clearChat() {
  messages.value = []
}
</script>
