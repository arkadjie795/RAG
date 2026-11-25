"""
BPS OCR Fallback Handler.
Provides OCR-based statistical table and narrative text extraction
for scanned or vector-flattened PDF publications where digital font streams are absent.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import pandas as pd
import fitz # PyMuPDF
from rapidocr_onnxruntime import RapidOCR

from modules.extraction.table_cleaner import TableCleaner


class BPSOCRHandler:
    """OCR handler leveraging RapidOCR for BPS tabular and narrative extraction."""

    _engine: Optional[RapidOCR] = None

    def __init__(self, dpi: int = 150):
        self.dpi = dpi
        self.cleaner = TableCleaner()
        if BPSOCRHandler._engine is None:
            logger.info("Initializing RapidOCR ONNX engine for BPS documents...")
            BPSOCRHandler._engine = RapidOCR(rec_batch_num=32)
        self.engine = BPSOCRHandler._engine

    @staticmethod
    def is_document_flattened(pdf_path: Path, sample_pages: int = 10) -> bool:
        """
        Detects whether a PDF consists of scanned/flattened vector graphics rather than digital text.
        """
        try:
            with fitz.open(str(pdf_path)) as doc:
                total_pages = len(doc)
                pages_to_check = min(sample_pages, total_pages)
                char_counts = []
                for i in range(pages_to_check):
                    txt = doc[i].get_text() or ""
                    # Strip watermark patterns to see true digital text content
                    txt_clean = re.sub(r"(?i)https?://[^\s]+|demakkab\.bps\.go\.id", "", txt)
                    char_counts.append(len(txt_clean.strip()))

                avg_chars = sum(char_counts) / len(char_counts) if char_counts else 0
                return avg_chars < 30
        except Exception as e:
            logger.error(f"Error checking PDF flattening: {e}")
            return False

    def ocr_page(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """Renders page to pixmap and runs OCR detection & recognition."""
        pix = page.get_pixmap(dpi=self.dpi)
        img_bytes = pix.tobytes("png")
        results, _ = self.engine(img_bytes)
        if not results:
            return []

        boxes = []
        for line in results:
            pts, text, score = line
            text = text.strip()
            if not text:
                continue
            x0 = min(p[0] for p in pts)
            x1 = max(p[0] for p in pts)
            y0 = min(p[1] for p in pts)
            y1 = max(p[1] for p in pts)
            boxes.append({
                "text": text,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "xc": (x0 + x1) / 2,
                "yc": (y0 + y1) / 2,
                "score": score
            })
        return boxes

    def _group_into_lines(self, boxes: List[Dict[str, Any]], y_tolerance: float = 14.0) -> List[Dict[str, Any]]:
        """Groups bounding boxes into horizontal lines based on y-coordinate proximity."""
        lines = []
        for b in sorted(boxes, key=lambda bx: (bx["y0"], bx["x0"])):
            yc = b["yc"]
            matched = False
            for line in lines:
                if abs(line["yc"] - yc) < y_tolerance:
                    line["boxes"].append(b)
                    line["yc"] = sum(bx["yc"] for bx in line["boxes"]) / len(line["boxes"])
                    matched = True
                    break
            if not matched:
                lines.append({"yc": yc, "boxes": [b]})

        lines = sorted(lines, key=lambda l: l["yc"])
        for l in lines:
            l["boxes"] = sorted(l["boxes"], key=lambda b: b["x0"])
            l["text"] = " ".join(b["text"] for b in l["boxes"])
        return lines

    def extract_table_from_page(self, boxes: List[Dict[str, Any]], page_num: int) -> Optional[Dict[str, Any]]:
        """
        Parses OCR text boxes on a single page into a structured statistical table.
        """
        lines = self._group_into_lines(boxes, y_tolerance=14.0)
        if not lines:
            return None

        # 1. Identify Table Title
        has_table_title = False
        title_parts = []
        num_row_idx = -1
        col_x_anchors = []
        source = "BPS"
        satuan = "N/A"
        catatan = ""

        # Check for column numbering row (1) (2) (3) ...
        for idx, l in enumerate(lines):
            line_txt = l["text"]
            matches = re.findall(r"\(\s*([0-9a-zA-Z])\s*\)", line_txt)
            if len(matches) >= 2 and matches[0] == "1":
                num_row_idx = idx
                for b in l["boxes"]:
                    m = re.match(r"^\(?\s*([0-9a-zA-Z])\s*\)?$", b["text"])
                    if m:
                        col_x_anchors.append(b["xc"])
                break

        # Check if table keyword is present
        for idx, l in enumerate(lines):
            ltxt = l["text"]
            if any(w in ltxt.lower() for w in ["tabel", "table", "lanjutan tabel", "continued table"]):
                has_table_title = True
                break

        if not has_table_title:
            return None

        # Identify title lines vs header lines vs data lines
        title_lines = []
        header_lines = []
        data_lines = []
        title_bottom_yc = 0.0
        num_row_yc = lines[num_row_idx]["yc"] if num_row_idx != -1 else 0.0

        for idx, l in enumerate(lines):
            ltxt = l["text"].strip()
            # Filter watermark and running header/footer
            if "demakkab.bps.go.id" in ltxt.lower() or TableCleaner.is_watermark_noise(ltxt):
                continue
            if re.match(r"^(bab\s+[ivxlcdm]+|\d+\s+[a-z\s]+)$", ltxt, re.IGNORECASE):
                continue
            if "geografi" in ltxt.lower() and "iklim" in ltxt.lower() or "geography and climate" in ltxt.lower():
                continue

            # Detect source / footnote
            if ltxt.lower().startswith("sumber") or ltxt.lower().startswith("source"):
                source = ltxt
                continue
            if ltxt.lower().startswith("catatan") or ltxt.lower().startswith("note"):
                catatan = ltxt
                continue

            if num_row_idx != -1:
                if idx < num_row_idx:
                    # Is it part of the table title or column header?
                    # Title lines are near the top of the table section
                    if any(w in ltxt.lower() for w in ["tabel", "table", "lanjutan"]):
                        title_parts.append(ltxt)
                        title_bottom_yc = max(title_bottom_yc, l["yc"])
                    elif not title_parts:
                        # Before table keyword
                        continue
                    elif l["yc"] <= title_bottom_yc + 80 and not any(w in ltxt.lower() for w in ["desa", "kelurahan", "persentase", "jumlah", "luas"]):
                        # Subtitle continuation
                        title_parts.append(ltxt)
                        title_bottom_yc = max(title_bottom_yc, l["yc"])
                    elif (num_row_yc - l["yc"]) <= 140:
                        header_lines.append(l)
                elif idx > num_row_idx:
                    data_lines.append(l)
            else:
                # Fallback without explicit (1) (2) row
                if any(w in ltxt.lower() for w in ["tabel", "table"]):
                    title_parts.append(ltxt)
                elif any(c.isdigit() for c in ltxt) and len(l["boxes"]) >= 2:
                    data_lines.append(l)
                else:
                    header_lines.append(l)

        # Assemble clean table title
        table_title = " ".join(title_parts).strip()
        table_title = re.sub(r"\s+", " ", table_title)
        # Remove redundant English labels in title
        table_title = re.sub(r"(?i)\b(table|continued table)\b", "", table_title).strip()
        if not table_title:
            table_title = f"Tabel Halaman {page_num}"

        # Detect unit of measurement
        unit_match = re.search(r"\((persen|%|ribu|ton|hektar|ha|km2|rupiah|jiwa|orang|unit|buah|kg)\)", table_title, re.IGNORECASE)
        if unit_match:
            satuan = unit_match.group(1)

        # Build column intervals and verify anchors against data lines
        valid_dl = [l for l in data_lines if len(l["boxes"]) >= 2]
        median_dl_boxes = int(pd.Series([len(l["boxes"]) for l in valid_dl]).median()) if valid_dl else 0
        if len(col_x_anchors) < median_dl_boxes or len(col_x_anchors) < 2:
            all_xc = []
            for dl in valid_dl:
                for b in dl["boxes"]:
                    all_xc.append(b["xc"])
            all_xc = sorted(all_xc)
            clustered = []
            for x in all_xc:
                matched = False
                for c in clustered:
                    if abs(c["mean"] - x) < 45:
                        c["vals"].append(x)
                        c["mean"] = sum(c["vals"]) / len(c["vals"])
                        matched = True
                        break
                if not matched:
                    clustered.append({"mean": x, "vals": [x]})
            min_support = max(2, len(valid_dl) * 0.25)
            anchors = [c["mean"] for c in clustered if len(c["vals"]) >= min_support]
            if len(anchors) >= 2:
                col_x_anchors = sorted(anchors)

        num_cols = len(col_x_anchors)
        if num_cols < 2:
            return None

        # Calculate column boundaries
        bounds = [(col_x_anchors[i] + col_x_anchors[i+1]) / 2 for i in range(len(col_x_anchors) - 1)]

        # Extract data rows
        rows = []
        for l in data_lines:
            ltxt = l["text"].strip()
            # Stop if reached running footer or source
            if ltxt.lower().startswith("sumber") or ltxt.lower().startswith("source") or "bps" in ltxt.lower() and len(ltxt) < 15:
                continue
            if "demakkab.bps.go.id" in ltxt.lower():
                continue

            row_cells = ["" for _ in range(num_cols)]
            for b in l["boxes"]:
                xc = b["xc"]
                col_idx = 0
                for b_idx, bound in enumerate(bounds):
                    if xc > bound:
                        col_idx = b_idx + 1
                cleaned_val = TableCleaner.clean_cell_text(b["text"])
                if row_cells[col_idx]:
                    row_cells[col_idx] += " " + cleaned_val
                else:
                    row_cells[col_idx] = cleaned_val

            # Filter out lines that are purely text labels spanning only 1 column after data started
            filled = [c for c in row_cells if c]
            if len(filled) == 1 and not any(ch.isdigit() for ch in filled[0]):
                # Footnote line or section header
                continue

            if any(row_cells):
                rows.append(row_cells)

        if not rows:
            return None

        # Build headers
        col_headers = [[] for _ in range(num_cols)]
        for hl in header_lines:
            for b in hl["boxes"]:
                xc = b["xc"]
                col_idx = 0
                for b_idx, bound in enumerate(bounds):
                    if xc > bound:
                        col_idx = b_idx + 1
                col_headers[col_idx].append(TableCleaner.clean_cell_text(b["text"]))

        final_headers = []
        for i, h in enumerate(col_headers):
            h_text = " ".join(h).strip()
            # Clean bilingual duplicates
            if not h_text or h_text in ["(1)", "(2)", "(3)", "(4)", "(5)"]:
                h_text = f"Kolom_{i+1}"
            final_headers.append(h_text)

        # Standardize First Column as Desa/Kelurahan or Wilayah if applicable
        if final_headers and ("desa" in final_headers[0].lower() or "kelurahan" in final_headers[0].lower() or final_headers[0].startswith("Kolom_1")):
            final_headers[0] = "Desa_Kelurahan"

        # Create raw matrix: header row + data rows
        raw_matrix = [final_headers] + rows
        cleaned_df = self.cleaner.clean_table_dataframe(raw_matrix, header_depth=1)
        if cleaned_df is None or len(cleaned_df) == 0:
            return None

        # Validate statistical table integrity
        if not self.cleaner.is_valid_statistical_table(cleaned_df, table_title):
            return None

        return {
            "tabel_id": f"p{page_num}_t1",
            "halaman": page_num,
            "judul_tabel": table_title,
            "satuan": satuan,
            "sumber": source,
            "catatan": catatan,
            "kolom": list(cleaned_df.columns),
            "jumlah_baris": len(cleaned_df),
            "dataframe": cleaned_df,
            "records": cleaned_df.to_dict(orient="records"),
            "bbox": (50.0, 100.0, 500.0, 700.0)
        }

    def extract_narratives_from_page(self, boxes: List[Dict[str, Any]], page_num: int) -> List[Dict[str, Any]]:
        """Parses OCR text boxes into clean narrative text paragraphs."""
        lines = self._group_into_lines(boxes, y_tolerance=12.0)
        if not lines:
            return []

        # If page is a table page, do not treat table data as narrative text
        has_table = any("tabel" in l["text"].lower() or "(1)" in l["text"] and "(2)" in l["text"] for l in lines)
        if has_table:
            return []

        # If page is a TOC / Daftar Isi / Daftar Tabel / Front Matter, skip narrative parsing
        page_raw_lower = " ".join(l["text"] for l in lines).lower()
        if any(kw in page_raw_lower for kw in [
            "daftar isi", "daftar tabel", "daftar gambar", "daftar grafik", 
            "daftar lampiran", "halaman page", "halaman/page", "table of contents",
            "list of tables", "list of figures"
        ]):
            return []

        narrative_blocks = []
        current_para = []

        for l in lines:
            ltxt = l["text"].strip()
            if not ltxt or TableCleaner.is_watermark_noise(ltxt) or "demakkab.bps.go.id" in ltxt.lower():
                continue
            if re.match(r"^\d+$", ltxt): # Pure page number
                continue

            cleaned_line = TableCleaner.clean_cell_text(ltxt)
            current_para.append(cleaned_line)

            if cleaned_line.endswith((".", "!", "?", ":")):
                full_text = " ".join(current_para).strip()
                if len(full_text) > 40 and not TableCleaner.is_watermark_noise(full_text):
                    narrative_blocks.append({
                        "halaman": page_num,
                        "bab": "Ringkasan Eksekutif",
                        "sub_bab": "Penjelasan Deskriptif",
                        "tipe_konten": "teks_naratif",
                        "teks": full_text
                    })
                current_para = []

        if current_para:
            full_text = " ".join(current_para).strip()
            if len(full_text) > 40 and not TableCleaner.is_watermark_noise(full_text):
                narrative_blocks.append({
                    "halaman": page_num,
                    "bab": "Ringkasan Eksekutif",
                    "sub_bab": "Penjelasan Deskriptif",
                    "tipe_konten": "teks_naratif",
                    "teks": full_text
                })

        return narrative_blocks

    def extract_tables_and_texts_from_pdf(
        self,
        pdf_path: Path,
        pages_to_extract: Optional[List[int]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes a full flattened/scanned PDF using RapidOCR.
        """
        pdf_path = Path(pdf_path)
        tables = []
        texts = []

        logger.info(f"Opening PDF for OCR extraction: {pdf_path.name}")
        with fitz.open(str(pdf_path)) as doc:
            total_pages = len(doc)
            target_pages = pages_to_extract if pages_to_extract else list(range(1, total_pages + 1))

            for page_num in target_pages:
                if page_num < 1 or page_num > total_pages:
                    continue

                page = doc[page_num - 1]
                # Skip pages that have almost no graphical drawings or content (cover back, blank separators)
                if len(page.get_drawings()) < 5 and len(page.get_images()) == 0:
                    continue

                try:
                    boxes = self.ocr_page(page)
                    if not boxes:
                        continue

                    # Try table extraction
                    table_obj = self.extract_table_from_page(boxes, page_num)
                    if table_obj:
                        tables.append(table_obj)
                        logger.info(
                            f"  [OCR Table Extracted] p{page_num}: {table_obj['judul_tabel'][:60]} "
                            f"({table_obj['jumlah_baris']} baris)"
                        )
                    else:
                        # Try narrative extraction
                        narratives = self.extract_narratives_from_page(boxes, page_num)
                        for n in narratives:
                            texts.append(n)
                except Exception as e:
                    logger.debug(f"OCR error on page {page_num}: {e}")
                    continue

        logger.info(f"OCR completed for {pdf_path.name}: {len(tables)} tables, {len(texts)} narrative text blocks.")
        return tables, texts
