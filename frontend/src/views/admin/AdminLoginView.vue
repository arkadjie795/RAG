<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
    <div class="max-w-md w-full bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
      <!-- Header -->
      <div class="text-center space-y-2">
        <img
          src="https://upload.wikimedia.org/wikipedia/commons/2/28/Lambang_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg"
          alt="Logo BPS"
          class="h-12 w-auto mx-auto"
        />
        <h2 class="text-xl font-black text-slate-900 tracking-tight">Admin Command Center</h2>
        <p class="text-xs text-slate-500">
          Autentikasi Internal Pengelola Data BPS Kabupaten Demak
        </p>
      </div>

      <!-- Error Alert if any -->
      <div v-if="errorMessage" class="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 shrink-0 text-red-500" />
        <span>{{ errorMessage }}</span>
      </div>

      <!-- PRIMARY: SIPETRA SSO (OAuth2) BUTTON -->
      <div class="space-y-3">
        <button
          type="button"
          @click="loginWithSipetra"
          :disabled="isLoggingIn"
          class="w-full flex items-center justify-center space-x-3 py-3 px-4 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer disabled:opacity-50"
        >
          <KeyRound class="w-4 h-4" />
          <span>Masuk dengan SIPETRA SSO (bpsdemak.com)</span>
        </button>
        <p class="text-[11px] text-slate-400 text-center">
          Login terpusat menggunakan akun resmi pegawai BPS Kabupaten Demak
        </p>
      </div>

      <!-- DIVIDER -->
      <div class="relative flex items-center justify-center">
        <div class="w-full border-t border-slate-200"></div>
        <div class="absolute px-3 bg-white text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          atau mode pengembang
        </div>
      </div>

      <!-- SECONDARY: LOCAL MOCK LOGIN FORM -->
      <form @submit.prevent="handleMockLogin" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Username Pengembang / Admin:</label>
          <input
            v-model="mockUsername"
            type="text"
            required
            placeholder="admin_bps"
            class="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 text-slate-800"
          />
        </div>

        <button
          type="submit"
          :disabled="isLoggingIn"
          class="w-full py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 rounded-xl text-xs font-semibold transition cursor-pointer"
        >
          {{ isLoggingIn ? 'Memproses...' : 'Masuk Langsung (Local Mock Session)' }}
        </button>
      </form>

      <!-- Return link -->
      <div class="pt-2 text-center border-t border-slate-100">
        <router-link to="/" class="text-xs text-sky-700 hover:underline font-medium">
          ← Kembali ke Portal Publik Sahabat Data
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { KeyRound, AlertCircle } from 'lucide-vue-next'
import { loginMockAdmin, getSipetraRedirectInfo } from '../../lib/api'

const router = useRouter()
const route = useRoute()

const mockUsername = ref('admin_bps')
const isLoggingIn = ref(false)
const errorMessage = ref('')

onMounted(() => {
  if (route.query.error) {
    if (route.query.error === 'sso_cancelled') {
      errorMessage.value = 'Login SIPETRA SSO dibatalkan oleh pengguna.'
    } else {
      errorMessage.value = `Terjadi kendala autentikasi: ${route.query.error}`
    }
  }
})

async function loginWithSipetra() {
  isLoggingIn.value = true
  errorMessage.value = ''
  try {
    const res = await getSipetraRedirectInfo()
    if (res.auth_url) {
      window.location.href = res.auth_url
    } else {
      errorMessage.value = 'URL redirect SIPETRA belum dapat dibuat.'
    }
  } catch (err) {
    errorMessage.value = `Gagal memicu SIPETRA SSO: ${err.message}`
  } finally {
    isLoggingIn.value = false
  }
}

async function handleMockLogin() {
  isLoggingIn.value = true
  errorMessage.value = ''
  try {
    await loginMockAdmin(mockUsername.value.trim() || 'admin_bps')
    const redirectPath = route.query.redirect || '/admin/ingestion'
    router.push(redirectPath)
  } catch (err) {
    errorMessage.value = `Gagal login: ${err.message}`
  } finally {
    isLoggingIn.value = false
  }
}
</script>
