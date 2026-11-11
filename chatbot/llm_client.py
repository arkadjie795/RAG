"""
Unified LLM Client using HTTPX.
Zero extra heavy SDK requirements; seamlessly supports Google Gemini, OpenAI,
Groq, Ollama / Local LLM, and Mock/Dry-run modes.
"""
import os
import httpx
from typing import Optional
from loguru import logger
from chatbot.config import bot_config


class LLMClient:
    """Unified client for invoking language models across multiple providers."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or bot_config.LLM_PROVIDER).lower()
        self.client = httpx.Client(timeout=60.0)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """Dispatches generation request to the configured provider."""
        # Check if provider can run or needs fallback to mock
        if self.provider == "gemini":
            api_key = bot_config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("[LLMClient] No GEMINI_API_KEY found in environment. Falling back to Dry-Run/Mock response.")
                return self._generate_mock(prompt, system_prompt, reason="GEMINI_API_KEY is not set in .env")
            return self._call_gemini(prompt, system_prompt, api_key)

        elif self.provider in ("openai", "groq", "ollama"):
            return self._call_openai_compatible(prompt, system_prompt)

        elif self.provider == "mock":
            return self._generate_mock(prompt, system_prompt, reason="Configured in MOCK mode")

        else:
            logger.warning(f"[LLMClient] Unknown provider '{self.provider}'. Falling back to mock.")
            return self._generate_mock(prompt, system_prompt, reason=f"Unsupported provider {self.provider}")

    def _call_gemini(self, prompt: str, system_prompt: str, api_key: str) -> str:
        """Calls Google Gemini REST API with automatic resilient fallback."""
        primary_model = bot_config.GEMINI_MODEL or "gemini-3.1-flash-lite"
        candidates_to_try = [primary_model]
        for backup in ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"]:
            if backup not in candidates_to_try:
                candidates_to_try.append(backup)

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }

        last_error = None
        for model in candidates_to_try:
            gen_config = {
                "temperature": bot_config.TEMPERATURE,
                "maxOutputTokens": bot_config.MAX_TOKENS
            }
            # Only send thinkingConfig if the model specifically targets thinking
            if "thinking" in model.lower():
                gen_config["thinkingConfig"] = {"thinkingBudget": 1024}

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "systemInstruction": {
                    "parts": [{"text": system_prompt}]
                },
                "generationConfig": gen_config
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                resp = self.client.post(url, headers=headers, params={"key": api_key}, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        cand = candidates[0]
                        finish_reason = cand.get("finishReason", "")
                        if finish_reason == "MAX_TOKENS":
                            logger.warning("[LLMClient] Model output reached MAX_TOKENS limit.")
                        text_parts = cand.get("content", {}).get("parts", [])
                        clean_parts = [p.get("text", "") for p in text_parts if not p.get("thought", False)]
                        if not clean_parts:
                            clean_parts = [p.get("text", "") for p in text_parts]
                        return "".join(clean_parts).strip()
                    return "Maaf, tidak ada tanggapan yang dihasilkan oleh model Gemini."
                else:
                    last_error = f"{resp.status_code}: {resp.text[:120]}"
                    logger.warning(f"[LLMClient] Model '{model}' returned status {resp.status_code}. Trying next candidate...")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[LLMClient] Model '{model}' request failed ({e}). Trying next candidate...")

        logger.error(f"[LLMClient] All Gemini model attempts failed. Last error: {last_error}")
        return f"[Error Gemini API]: Semua model gagal merespons ({last_error}). Silakan periksa koneksi internet atau kuota API Key Anda."

    def _call_openai_compatible(self, prompt: str, system_prompt: str) -> str:
        """Invokes OpenAI, Groq, or Ollama via standard chat completions format."""
        if self.provider == "openai":
            base_url = bot_config.OPENAI_BASE_URL or "https://api.openai.com/v1"
            api_key = bot_config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            model = bot_config.OPENAI_MODEL
        elif self.provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
            api_key = bot_config.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
            model = bot_config.GROQ_MODEL
        elif self.provider == "ollama":
            base_url = f"{bot_config.OLLAMA_BASE_URL}/v1"
            api_key = "ollama"
            model = bot_config.OLLAMA_MODEL
        else:
            return self._generate_mock(prompt, system_prompt, reason="Invalid provider mapping")

        if not api_key and self.provider != "ollama":
            logger.warning(f"[LLMClient] No API key found for provider '{self.provider}'. Falling back to Mock mode.")
            return self._generate_mock(prompt, system_prompt, reason=f"{self.provider.upper()}_API_KEY is not set.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": bot_config.TEMPERATURE,
            "max_tokens": bot_config.MAX_TOKENS
        }

        url = f"{base_url.rstrip('/')}/chat/completions"
        try:
            resp = self.client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                return "Maaf, tidak ada teks jawaban yang dikembalikan provider."
            else:
                logger.error(f"[LLMClient] Provider '{self.provider}' returned HTTP {resp.status_code}: {resp.text}")
                return f"[Error {self.provider.capitalize()} API]: Terjadi kendala HTTP {resp.status_code} saat mengakses model."
        except Exception as e:
            logger.error(f"[LLMClient] Request to {self.provider} failed: {e}")
            return f"[Error Koneksi]: Gagal menghubungi layanan {self.provider.capitalize()} ({e})."

    def _generate_mock(self, prompt: str, system_prompt: str, reason: str = "") -> str:
        """Returns a deterministic, formatted preview response for verification and tests."""
        logger.info(f"[LLMClient] Generating simulated response ({reason})")
        return (
            f"[Mode Simulasi / Dry-Run (Alasan: {reason})]\n\n"
            f"Halo! Saya adalah Sahabat Data BPS Kabupaten Demak. Permintaan Anda telah diterima dan "
            f"diproses melalui pipeline verifikasi data. Untuk mengaktifkan respon cerdas berbasis AI generatif, "
            f"silakan konfigurasikan API Key resmi pada berkas `.env`."
        )
