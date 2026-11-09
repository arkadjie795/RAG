<template>
  <div class="min-h-screen flex flex-col bg-slate-50 text-slate-800">
    <!-- ========================================== -->
    <!-- PUBLIC PORTAL HEADER -->
    <!-- ========================================== -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo & Branding -->
        <div class="flex items-center space-x-3">
          <img
            src="https://upload.wikimedia.org/wikipedia/commons/2/28/Lambang_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg"
            alt="Logo BPS"
            class="h-9 w-auto"
          />
          <div>
            <div class="flex items-center space-x-2">
              <span class="font-extrabold text-base sm:text-lg text-slate-900 tracking-tight">Sahabat Data</span>
              <span class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-orange-100 text-orange-800 border border-orange-200">
                BPS Demak 3321
              </span>
            </div>
            <p class="text-[11px] text-slate-500 hidden sm:block">
              Layanan Informasi & Konsultasi Statistik Resmi Berbasis AI
            </p>
          </div>
        </div>

        <!-- Right Quick Actions -->
        <div class="flex items-center space-x-2 sm:space-x-3">
          <a
            href="https://demakkab.bps.go.id"
            target="_blank"
            rel="noopener noreferrer"
            class="hidden md:inline-flex items-center text-xs font-medium text-slate-600 hover:text-sky-700 transition px-2.5 py-1.5 rounded-lg hover:bg-slate-100"
          >
            <span>Portal BPS Demak</span>
            <ExternalLink class="w-3.5 h-3.5 ml-1 text-slate-400" />
          </a>

          <div class="h-4 w-px bg-slate-200 hidden md:block"></div>

          <!-- Link to Admin Command Center -->
          <router-link
            to="/admin"
            class="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 transition"
          >
            <ShieldCheck class="w-3.5 h-3.5 text-sky-700" />
            <span>Admin / PST</span>
          </router-link>
        </div>
      </div>
    </header>

    <!-- MAIN VIEW AREA -->
    <main class="flex-1 flex flex-col">
      <router-view />
    </main>

    <!-- FOOTER -->
    <footer class="bg-white border-t border-slate-200 py-4 px-4 text-center text-xs text-slate-500">
      <p>
        © 2026 Badan Pusat Statistik Kabupaten Demak | Jl. Kyai Singkil No. 23 Demak | Telp: (0291) 685121
      </p>
    </footer>
  </div>
</template>

<script setup>
import { ExternalLink, ShieldCheck } from 'lucide-vue-next'
</script>
