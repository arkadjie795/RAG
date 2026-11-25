"""
BPS Table Extractor Module.
Extracts complex and borderless tables from BPS PDFs using pdfplumber, captures contextual
titles, footnotes, and units, and transforms them into cleaned DataFrames.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pdfplumber
import pandas as pd
from loguru import logger

from modules.extraction.table_cleaner import TableCleaner
from config.settings import settings


class BPSTableExtractor:
    """Extracts and contextualizes tables from BPS publication PDFs."""

    def __init__(self):
        self.cleaner = TableCleaner()

    @staticmethod
    def is_clean_char(obj: Dict[str, Any]) -> bool:
        """Filters out rotated or oversized watermark characters without modifying genuine content."""
        if obj.get("object_type") == "char":
            m = obj.get("matrix", (1, 0, 0, 1))
            # Diagonal or rotated character (BPS watermark is diagonal dir (0.7071, -0.7071))
            if abs(m[1]) > 0.05 or abs(m[2]) > 0.05:
                return False
            # Big watermark font size (> 18 pt)
            if obj.get("size", 0) > 18:
                return False
            # Explicit domain text
            if "demakkab" in obj.get("text", "").lower():
                return False
        return True

    def _extract_table_context(
        self, 
        page: pdfplumber.page.Page, 
        table_bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict[str, str]:
        """
        Extracts metadata surrounding a table on a PDF page:
        - Table title (above the table)
        - Unit / Satuan (e.g., '(Jiwa)', '(Rupiah)', '(Ton)')
        - Source / Footnotes (below the table)
        """
        page_height = page.height
        page_width = page.width

        if table_bbox:
            x0, top, x1, bottom = table_bbox
        else:
            top = 130.0
            bottom = page_height - 90.0

        # 1. Look for Table Title above the table (top region: y in [0, top])
        table_title = "Tabel Statistik"
        unit = "N/A"
        above_text = ""

        crop_top_y0 = max(0.0, float(top) - 130.0)
        crop_top_y1 = max(0.0, float(top))
        if crop_top_y1 > crop_top_y0:
            try:
                above_crop = page.crop((0, crop_top_y0, page_width, crop_top_y1))
                above_text = above_crop.extract_text(layout=False) or ""
            except Exception as e:
                logger.debug(f"Above table crop skipped: {e}")

        # Regex to capture BPS table naming pattern (e.g., "Tabel 3.1.1 Jumlah Penduduk...")
        title_match = re.search(
            r"(Tabel|Table)\s+[\d\.]+\s*[:\.]?\s*[^\n]+(?:\n[^\n]+)?",
            above_text,
            re.IGNORECASE
        )
        if title_match:
            table_title = re.sub(r"\s+", " ", title_match.group(0)).strip()
        else:
            # Fallback to the whole page text searching for Tabel pattern
            full_txt = page.extract_text(layout=False) or ""
            page_title_match = re.search(r"(Tabel|Table)\s+[\d\.]+\s*[:\.]?\s*[^\n]+", full_txt, re.IGNORECASE)
            if page_title_match:
                table_title = re.sub(r"\s+", " ", page_title_match.group(0)).strip()
            else:
                lines = [l.strip() for l in above_text.splitlines() if l.strip()]
                if lines:
                    table_title = lines[-1]

        # Extract unit / satuan e.g. '(Jiwa)', '(Persen)', '(Hektar)'
        unit_match = re.search(r"/\s*([A-Za-z\s%]+)|\(([A-Za-z\s%]+)\)", table_title)
        if unit_match:
            unit = (unit_match.group(1) or unit_match.group(2) or "").strip()

        # 2. Look for Source / Notes below the table
        below_text = ""
        crop_bot_y0 = min(float(page_height), max(0.0, float(bottom)))
        crop_bot_y1 = min(float(page_height), max(0.0, float(bottom) + 110.0))
        if crop_bot_y1 > crop_bot_y0:
            try:
                below_crop = page.crop((0, crop_bot_y0, page_width, crop_bot_y1))
                below_text = below_crop.extract_text(layout=False) or ""
            except Exception as e:
                logger.debug(f"Below table crop skipped: {e}")

        source = "BPS"
        notes = ""

        # Check in below_text or full page
        search_text = below_text or (page.extract_text(layout=False) or "")
        for line in search_text.splitlines():
            line_str = line.strip()
            if re.search(r"^Sumber\s*[:\.]|^Source\s*[:\.]", line_str, re.IGNORECASE):
                source = re.sub(r"^Sumber\s*[:\.]\s*|^Source\s*[:\.]\s*", "", line_str, flags=re.IGNORECASE).strip()
            elif re.search(r"^Catatan\s*[:\.]|^Note\s*[:\.]", line_str, re.IGNORECASE):
                notes = re.sub(r"^Catatan\s*[:\.]\s*|^Note\s*[:\.]\s*", "", line_str, flags=re.IGNORECASE).strip()

        return {
            "judul_tabel": table_title,
            "satuan": unit,
            "sumber": source,
            "catatan": notes
        }

    def _extract_borderless_table(self, clean_page: pdfplumber.page.Page) -> Optional[List[List[Any]]]:
        """
        Heuristic line-clustering extractor for borderless BPS tables (e.g. Statistik Pendidikan,
        Kecamatan Dalam Angka without vertical grid lines).
        """
        words = clean_page.extract_words()
        if not words:
            return None

        # 1. Locate title position
        title_y = None
        for w in words:
            if re.search(r'^(Tabel|Table)$', w['text'], re.IGNORECASE):
                title_y = w['top']
                break
        if title_y is None:
            title_y = 60.0

        # 2. Locate source position (lower bound)
        source_y = clean_page.height - 60.0
        for w in words:
            if re.search(r'^(Sumber|Source)$', w['text'], re.IGNORECASE) and w['top'] > title_y + 100:
                source_y = min(source_y, w['top'])
                break

        # 3. Locate header lower bound using rects or words
        header_rects = [r for r in clean_page.rects if title_y <= r['top'] <= title_y + 120 and r['width'] > 20]
        if header_rects:
            header_top = min(r['top'] for r in header_rects) - 2
            header_bot = max(r['bottom'] for r in header_rects) + 2
        else:
            header_top = title_y + 20.0
            header_bot = title_y + 90.0

        # 4. Filter data words strictly inside table body
        data_words = [w for w in words if header_bot <= w['top'] < source_y]
        if not data_words:
            return None

        # 5. Group data words into lines (vertical tolerance 5 points)
        lines = []
        sorted_words = sorted(data_words, key=lambda x: x['top'])
        current_line = []
        current_top = None
        for w in sorted_words:
            if current_top is None:
                current_top = w['top']
                current_line.append(w)
            elif abs(w['top'] - current_top) <= 5:
                current_line.append(w)
            else:
                lines.append(sorted(current_line, key=lambda x: x['x0']))
                current_line = [w]
                current_top = w['top']
        if current_line:
            lines.append(sorted(current_line, key=lambda x: x['x0']))

        if len(lines) < 2:
            return None

        # Determine column count and representative column x-positions
        sample_line = max(lines, key=len)
        num_cols = len(sample_line)
        col_x = [w['x0'] for w in sample_line]

        # Extract header words into aligned header rows
        h_words = [w for w in words if header_top <= w['top'] <= header_bot]
        h_lines_dict = {}
        for w in sorted(h_words, key=lambda x: (x['top'], x['x0'])):
            top_k = round(w['top'] / 8) * 8
            h_lines_dict.setdefault(top_k, []).append(w)

        header_rows = []
        for top_k in sorted(h_lines_dict.keys()):
            h_row = ["" for _ in range(num_cols)]
            for w in h_lines_dict[top_k]:
                w_mid = (w['x0'] + w['x1']) / 2
                best_i = min(range(num_cols), key=lambda i: abs(col_x[i] - w_mid))
                h_row[best_i] = (h_row[best_i] + " " + w['text']).strip()
            header_rows.append(h_row)

        if not header_rows:
            header_rows = [[f"Kolom_{i+1}" for i in range(num_cols)]]
        header_rows[0][0] = "Wilayah_Kecamatan"

        # 6. Assemble raw matrix
        raw_matrix = []
        for l in lines:
            txts = [w['text'] for w in l]
            # Merge prefix 'Kab.' and 'Demak' if split
            if len(txts) >= 2 and txts[0] == "Kab." and txts[1] == "Demak":
                txts = ["Kab. Demak"] + txts[2:]
            while len(txts) < num_cols:
                txts.append("")
            raw_matrix.append(txts[:num_cols])

        full_matrix = header_rows + raw_matrix
        return full_matrix, len(header_rows)

    def extract_tables_from_pdf(
        self, 
        pdf_path: Path, 
        pages_to_extract: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts all verified statistical tables from a BPS publication PDF.
        Returns a list of structured table objects with clean DataFrame and metadata.
        """
        extracted_tables: List[Dict[str, Any]] = []

        if not Path(pdf_path).exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return extracted_tables

        logger.info(f"Opening PDF for table extraction: {pdf_path.name}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                max_pages = getattr(settings, "MAX_EXTRACT_PAGES", None)
                if pages_to_extract is not None:
                    page_indices = pages_to_extract
                elif max_pages:
                    page_indices = range(1, min(total_pages, max_pages) + 1)
                else:
                    page_indices = range(1, total_pages + 1)

                for page_num in page_indices:
                    if page_num > total_pages:
                        continue
                    
                    page = pdf.pages[page_num - 1]
                    clean_page = page.filter(self.is_clean_char)
                    page_text = clean_page.extract_text(layout=False) or ""

                    # Quick gatekeeper: check if page contains an official BPS table caption
                    has_table_title = bool(re.search(r'\b(Tabel|Table)\s+[\d\.]+', page_text, re.IGNORECASE))
                    has_explicit_lines = len(clean_page.lines) >= 4 or len(clean_page.rects) >= 4

                    if not has_table_title and not has_explicit_lines:
                        continue

                    # 1. Try extracting with pdfplumber grid-line finder
                    found_tables = clean_page.find_tables(
                        table_settings={
                            "vertical_strategy": "lines",
                            "horizontal_strategy": "lines",
                            "snap_tolerance": 3,
                            "join_tolerance": 3,
                            "edge_min_length": 10
                        }
                    )

                    page_table_added = False

                    if found_tables:
                        for t_idx, tbl in enumerate(found_tables):
                            try:
                                raw_matrix = tbl.extract()
                                if not raw_matrix or len(raw_matrix) < 3:
                                    continue

                                context = self._extract_table_context(clean_page, tbl.bbox)
                                cleaned_df = self.cleaner.clean_table_dataframe(raw_matrix)

                                if cleaned_df is not None and self.cleaner.is_valid_statistical_table(cleaned_df, context["judul_tabel"]):
                                    table_obj = {
                                        "tabel_id": f"p{page_num}_t{t_idx + 1}",
                                        "halaman": page_num,
                                        "judul_tabel": context["judul_tabel"],
                                        "satuan": context["satuan"],
                                        "sumber": context["sumber"],
                                        "catatan": context["catatan"],
                                        "kolom": list(cleaned_df.columns),
                                        "jumlah_baris": len(cleaned_df),
                                        "dataframe": cleaned_df,
                                        "records": cleaned_df.to_dict(orient="records"),
                                        "bbox": tbl.bbox
                                    }
                                    extracted_tables.append(table_obj)
                                    page_table_added = True
                            except Exception as tbl_err:
                                logger.debug(f"Failed grid extraction on p{page_num}: {tbl_err}")
                                continue

                    # 2. If no valid table was extracted via grid lines, but page has an official Table title:
                    # Fallback to borderless table extractor
                    if not page_table_added and has_table_title:
                        try:
                            context = self._extract_table_context(clean_page)
                            border_res = self._extract_borderless_table(clean_page)
                            if border_res:
                                raw_mat, h_depth = border_res
                                cleaned_df = self.cleaner.clean_table_dataframe(raw_mat, header_depth=h_depth)
                                if cleaned_df is not None and self.cleaner.is_valid_statistical_table(cleaned_df, context["judul_tabel"]):
                                    table_obj = {
                                        "tabel_id": f"p{page_num}_t1",
                                        "halaman": page_num,
                                        "judul_tabel": context["judul_tabel"],
                                        "satuan": context["satuan"],
                                        "sumber": context["sumber"],
                                        "catatan": context["catatan"],
                                        "kolom": list(cleaned_df.columns),
                                        "jumlah_baris": len(cleaned_df),
                                        "dataframe": cleaned_df,
                                        "records": cleaned_df.to_dict(orient="records"),
                                        "bbox": (80.0, 120.0, clean_page.width - 80.0, clean_page.height - 120.0)
                                    }
                                    extracted_tables.append(table_obj)
                        except Exception as border_err:
                            logger.debug(f"Failed borderless extraction on p{page_num}: {border_err}")

            logger.info(f"Successfully extracted {len(extracted_tables)} verified tables from {pdf_path.name}")

        except Exception as e:
            logger.error(f"Error extracting tables from {pdf_path.name}: {e}")

        return extracted_tables
