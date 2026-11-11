"""
Ingestion & Scraper Job Controller Router for BPS Demak Data Pipeline.
Executes crawler tasks non-blockingly and exposes real-time state telemetry.
"""
import threading
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/api/ingestion", tags=["Data Ingestion & Scraper Hub"])


class ScraperRunRequest(BaseModel):
    mode: str = "statis"  # statis, all, or pdf
    max_pages: Optional[int] = 2
    pdf_path: Optional[str] = None


class IngestionJobState:
    """Thread-safe singleton tracking crawler background execution."""

    def __init__(self):
        self.lock = threading.Lock()
        self.status: str = "IDLE"  # IDLE, RUNNING, COMPLETED, FAILED, STOPPED
        self.mode: str = "statis"
        self.job_id: Optional[str] = None
        self.progress_pct: int = 0
        self.current_phase: str = "Siap dijalankan"
        self.processed_items: int = 0
        self.total_items: int = 0
        self.error_message: Optional[str] = None
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.cancel_requested: bool = False
        self.recent_logs: list = []

    def log(self, message: str):
        with self.lock:
            timestamp = time.strftime("%H:%M:%S")
            self.recent_logs.append(f"[{timestamp}] {message}")
            if len(self.recent_logs) > 50:
                self.recent_logs.pop(0)

    def reset(self, job_id: str, mode: str):
        with self.lock:
            self.status = "RUNNING"
            self.mode = mode
            self.job_id = job_id
            self.progress_pct = 5
            self.current_phase = "Menginisialisasi pipeline BPS Demak..."
            self.processed_items = 0
            self.total_items = 0
            self.error_message = None
            self.started_at = time.time()
            self.finished_at = None
            self.cancel_requested = False
            self.recent_logs = []
            self.log(f"Job '{job_id}' dimulai dengan mode: {mode}")

    def update(self, phase: str, progress: int, processed: int = 0, total: int = 0):
        with self.lock:
            self.current_phase = phase
            self.progress_pct = min(100, max(0, progress))
            if processed:
                self.processed_items = processed
            if total:
                self.total_items = total
            self.log(f"{phase} ({self.progress_pct}%)")

    def finish(self, success: bool = True, err: Optional[str] = None):
        with self.lock:
            self.status = "COMPLETED" if success else "FAILED"
            self.finished_at = time.time()
            self.progress_pct = 100 if success else self.progress_pct
            self.current_phase = "Selesai" if success else f"Gagal: {err}"
            self.error_message = err
            self.log("Job selesai dengan sukses." if success else f"Job gagal: {err}")

    def to_dict(self) -> Dict[str, Any]:
        with self.lock:
            elapsed = round(time.time() - self.started_at, 1) if self.started_at and not self.finished_at else (
                round(self.finished_at - self.started_at, 1) if self.started_at and self.finished_at else 0
            )
            return {
                "status": self.status,
                "job_id": self.job_id,
                "mode": self.mode,
                "progress_pct": self.progress_pct,
                "current_phase": self.current_phase,
                "processed_items": self.processed_items,
                "total_items": self.total_items,
                "elapsed_seconds": elapsed,
                "error_message": self.error_message,
                "logs": list(self.recent_logs)
            }


# Global job tracker instance
job_manager = IngestionJobState()


def _run_crawler_task(mode: str, max_pages: int, pdf_path: Optional[str]):
    """Background task invoking master orchestrator pipeline safely."""
    try:
        job_manager.update("1. Memeriksa portal BPS & registri deduplikasi...", 10)
        from pathlib import Path
        from main import BPSPipelineOrchestrator

        orchestrator = BPSPipelineOrchestrator()
        job_manager.update(f"2. Menginisialisasi pipeline (Mode: {mode.upper()})...", 25)

        if job_manager.cancel_requested:
            job_manager.finish(success=False, err="Dibatalkan oleh admin")
            return

        if mode == "statis":
            job_manager.update(f"3. Menjalankan crawler katalog (maksimal {max_pages} halaman)...", 45)
            orchestrator.run_mode_statis(max_pages=max_pages)
        elif mode == "all":
            job_manager.update(f"3. Menjalankan crawler katalog historis ({max_pages} halaman)...", 45)
            orchestrator.run_mode_all(max_pages=max_pages)
        elif mode == "pdf" and pdf_path:
            target_path = Path(pdf_path)
            if not target_path.exists():
                job_manager.finish(success=False, err=f"File PDF tidak ditemukan: {pdf_path}")
                return
            job_manager.update(f"3. Mengekstrak dan mengindeks {target_path.name}...", 50)
            orchestrator.run_mode_single_pdf(target_path)
        else:
            job_manager.update("3. Menjalankan proses pipeline standar...", 50)
            orchestrator.run_mode_statis(max_pages=max_pages)

        job_manager.update("4. Memfinalisasi indeks vektor dan tabel PostgreSQL...", 90)
        job_manager.finish(success=True)
    except Exception as ex:
        logger.error(f"[IngestionRouter] Error executing crawl task: {ex}")
        job_manager.finish(success=False, err=str(ex))


@router.get("/status")
def get_ingestion_status() -> Dict[str, Any]:
    """Returns real-time status, progress percentage, and logs of crawler job."""
    return job_manager.to_dict()


@router.post("/run")
def run_ingestion(req: ScraperRunRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Triggers crawler execution asynchronously in background thread."""
    if job_manager.status == "RUNNING":
        return {
            "status": "ALREADY_RUNNING",
            "message": "Scraper sedang berjalan, tunggu hingga proses selesai.",
            "data": job_manager.to_dict()
        }

    job_id = f"job_{req.mode}_{int(time.time())}"
    job_manager.reset(job_id=job_id, mode=req.mode)

    # Launch in background thread
    threading.Thread(
        target=_run_crawler_task,
        args=(req.mode, req.max_pages or 2, req.pdf_path),
        daemon=True
    ).start()

    return {
        "status": "RUNNING",
        "job_id": job_id,
        "mode": req.mode,
        "message": f"Job scraping '{job_id}' berhasil dipicu di latar belakang."
    }


@router.post("/stop")
def stop_ingestion() -> Dict[str, Any]:
    """Requests running scraper job to halt."""
    if job_manager.status != "RUNNING":
        return {"status": "NOT_RUNNING", "message": "Tidak ada job yang sedang berjalan."}

    job_manager.cancel_requested = True
    job_manager.status = "STOPPED"
    job_manager.log("Admin meminta penghentian scraper.")
    return {"status": "STOPPING", "message": "Permintaan pembatalan job berhasil dikirim."}
