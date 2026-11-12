"""
Official BPS Web API Client Module for BPS Demak (Domain 3321).
Directly interfaces with webapi.bps.go.id for authoritative publications and statistical tables,
eliminating HTML scraping and avoiding WAF/bot challenge blocking.
"""
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from loguru import logger

from config.settings import settings
from modules.ingestion.registry import PublicationRegistry


class BPSWebApiClient:
    """Official Web API Client for BPS Kabupaten Demak (Domain 3321)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        domain_id: Optional[str] = None,
        registry: Optional[PublicationRegistry] = None,
        target_dir: Optional[Path] = None
    ):
        self.api_key = api_key or getattr(settings, "BPS_API_KEY", "b73ea5437eb23fb8309858b840029da2")
        self.base_url = (base_url or getattr(settings, "BPS_API_BASE_URL", "https://webapi.bps.go.id/v1/api/")).rstrip("/")
        self.domain_id = domain_id or getattr(settings, "BPS_DOMAIN_ID", "3321")
        self.registry = registry or PublicationRegistry()
        self.target_dir = target_dir or settings.DEMAK_DATA_DIR

        self.client = httpx.Client(
            headers={
                "User-Agent": "BPS-Demak-Command-Center/2.0 (Official API Client)",
                "Accept": "application/json"
            },
            timeout=45.0,
            follow_redirects=True
        )

    def _slugify(self, text: str) -> str:
        """Converts arbitrary strings into safe filenames."""
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "_", text)
        return text.strip("_")[:80]

    def test_connection(self) -> bool:
        """Checks if BPS Web API is reachable and API key is valid."""
        try:
            url = f"{self.base_url}/list/model/publication/domain/{self.domain_id}/key/{self.api_key}/"
            resp = self.client.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("status") == "OK"
            return False
        except Exception as e:
            logger.warning(f"[BPSWebApiClient] Connection test failed: {e}")
            return False

    def fetch_publication_page(self, page: int = 1, year: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches one page of publications from BPS Web API.
        Example: /list/model/publication/domain/3321/page/1/key/...
        """
        if year:
            url = f"{self.base_url}/list/model/publication/domain/{self.domain_id}/page/{page}/year/{year}/key/{self.api_key}/"
        else:
            url = f"{self.base_url}/list/model/publication/domain/{self.domain_id}/page/{page}/key/{self.api_key}/"

        try:
            resp = self.client.get(url)
            if resp.status_code != 200:
                logger.error(f"[BPSWebApiClient] HTTP {resp.status_code} fetching page {page}")
                return {"items": [], "total": 0, "page": page, "pages": 0}

            data = resp.json()
            if data.get("status") != "OK" or not data.get("data"):
                return {"items": [], "total": 0, "page": page, "pages": 0}

            meta = data["data"][0] if len(data["data"]) > 0 else {}
            raw_pubs = data["data"][1] if len(data["data"]) > 1 else []

            cleaned_items = []
            for pub in raw_pubs:
                release_date = pub.get("rl_date") or pub.get("sch_date") or datetime.utcnow().strftime("%Y-%m-%d")
                pub_id = pub.get("pub_id")
                title = pub.get("title", "Publikasi BPS Demak")
                cleaned_items.append({
                    "publication_id": pub_id,
                    "title": title,
                    "release_date": release_date,
                    "category": pub.get("subj") or "Statistik Daerah",
                    "pdf_url": pub.get("pdf"),
                    "cover_url": pub.get("cover"),
                    "abstract": pub.get("abstract"),
                    "file_size": pub.get("size"),
                    "detail_url": f"https://demakkab.bps.go.id/id/publication/{pub_id}"
                })

            return {
                "items": cleaned_items,
                "total": meta.get("total", len(cleaned_items)),
                "page": meta.get("page", page),
                "pages": meta.get("pages", 1),
                "count": meta.get("count", len(cleaned_items))
            }
        except Exception as e:
            logger.error(f"[BPSWebApiClient] Error fetching publication page {page}: {e}")
            return {"items": [], "total": 0, "page": page, "pages": 0}

    def fetch_all_publications(self, max_pages: int = 5, year: Optional[str] = None) -> List[Dict[str, Any]]:
        """Iterates through publication pages up to max_pages."""
        all_items = []
        for p in range(1, max_pages + 1):
            logger.info(f"[BPSWebApiClient] Fetching official publications page {p}/{max_pages}...")
            res = self.fetch_publication_page(page=p, year=year)
            items = res.get("items", [])
            if not items:
                break
            all_items.extend(items)
            if p >= res.get("pages", 1):
                break
            time.sleep(0.3)  # Respect API rate limits gracefully

        logger.info(f"[BPSWebApiClient] Discovered {len(all_items)} publications from BPS Web API.")
        return all_items

    def download_publication_pdf(self, pub_meta: Dict[str, Any]) -> Optional[Path]:
        """
        Directly downloads official PDF stream from BPS Web API.
        Saves locally and registers in SQLite registry.
        """
        pub_id = pub_meta["publication_id"]
        title = pub_meta["title"]
        pdf_url = pub_meta.get("pdf_url")
        release_date = pub_meta.get("release_date", "2026-01-01")

        if not pdf_url:
            logger.warning(f"[BPSWebApiClient] No direct PDF URL for publication [{pub_id}] {title}")
            return None

        # Determine year/month subfolder
        try:
            year, month, _ = release_date.split("-")
        except Exception:
            year, month = "2026", "01"

        target_folder = self.target_dir / year / month
        target_folder.mkdir(parents=True, exist_ok=True)

        slug = self._slugify(title)[:60]
        filename = f"{pub_id}_{slug}.pdf"
        target_file_path = target_folder / filename

        # 1. Check existing disk file
        if target_file_path.exists() and target_file_path.stat().st_size > 1000:
            file_size = target_file_path.stat().st_size
            self.registry.register_or_update_metadata(pub_meta)
            self.registry.mark_download_success(pub_id, str(target_file_path), file_size)
            logger.info(f"[BPSWebApiClient] Using cached PDF on disk: {target_file_path.name}")
            return target_file_path

        # 2. Check if already in registry
        if self.registry.is_already_downloaded(pub_id):
            logger.info(f"[BPSWebApiClient] Skipping download (Already downloaded in registry): [{pub_id}] {title}")
            return None

        logger.info(f"[BPSWebApiClient] Downloading official PDF: [{pub_id}] '{title}' ({pub_meta.get('file_size', '')})...")
        try:
            with self.client.stream("GET", pdf_url, timeout=90.0) as resp:
                if resp.status_code != 200:
                    logger.warning(f"[BPSWebApiClient] HTTP {resp.status_code} downloading PDF for {pub_id}")
                    self.registry.mark_download_failed(pub_id)
                    return None

                with open(target_file_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=32768):
                        f.write(chunk)

            # Validate PDF integrity
            if target_file_path.exists():
                file_size = target_file_path.stat().st_size
                with open(target_file_path, "rb") as f:
                    header = f.read(10)
                if b"%PDF" in header and file_size > 1000:
                    logger.success(f"[BPSWebApiClient] Successfully downloaded {target_file_path.name} ({file_size:,} bytes).")
                    self.registry.register_or_update_metadata(pub_meta)
                    self.registry.mark_download_success(
                        publication_id=pub_id,
                        file_path=str(target_file_path),
                        file_size=file_size
                    )
                    return target_file_path
                else:
                    logger.warning(f"[BPSWebApiClient] Downloaded file for {pub_id} is invalid. Removing.")
                    target_file_path.unlink(missing_ok=True)

            self.registry.mark_download_failed(pub_id)
            return None
        except Exception as ex:
            logger.error(f"[BPSWebApiClient] Download exception for [{pub_id}]: {ex}")
            if target_file_path.exists():
                target_file_path.unlink(missing_ok=True)
            self.registry.mark_download_failed(pub_id)
            return None

    def run_api_ingestion(self, max_pages: int = 2, year: Optional[str] = None) -> List[Path]:
        """Runs complete ingestion cycle: discovers from API, downloads new PDFs, returns list of Paths."""
        publications = self.fetch_all_publications(max_pages=max_pages, year=year)
        downloaded_paths = []

        for pub in publications:
            path = self.download_publication_pdf(pub)
            if path:
                downloaded_paths.append(path)

        return downloaded_paths
