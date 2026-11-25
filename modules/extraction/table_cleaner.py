"""
Table Cleaner Module for BPS Statistical Tables.
Handles multi-index header flattening, contextual forward fill, watermark stripping,
and Indonesian BPS statistical symbol preservation.
"""
import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from loguru import logger


class ValueStatus(str, Enum):
    NORMAL_VALUE = "NORMAL_VALUE"
    ZERO = "ZERO"
    NIL = "NIL"                       # For '-', '–', '—' (data tidak ada / nihil)
    NEGLIGIBLE = "NEGLIGIBLE"         # For '0,0', '0,00' (sangat kecil / mendekati nol)
    NOT_AVAILABLE = "NOT_AVAILABLE"   # For '...', '…' (data belum tersedia)
    NOT_APPLICABLE = "NOT_APPLICABLE" # For 'NA', 'N/A' (tidak dapat diterapkan)
    PROVISIONAL = "PROVISIONAL"       # With '*', '*)' (angka sementara)
    REVISED = "REVISED"               # With 'r', 'R' (angka perbaikan/revisi)
    SUPPRESSED = "SUPPRESSED"         # Confidential / withheld
    TEXT = "TEXT"


@dataclass
class StatisticalCell:
    raw_value: str
    normalized_value: Optional[Union[int, float]]
    value_status: ValueStatus
    unit: Optional[str] = None
    footnote: Optional[str] = None
    revision_mark: Optional[str] = None


class TableCleaner:
    """Specialized data cleaner for BPS complex statistical tables."""

    @staticmethod
    def is_watermark_noise(s: str) -> bool:
        """Identifies if a string is solely BPS watermark debris (e.g. 'https://...', 'o g .', 's p', 'b .')."""
        s_clean = s.strip()
        if not s_clean:
            return True
        # Explicit URL or known artifact
        if re.search(r"https?://|demakkab\.bps\.go\.id|\bd_i__o_g\b", s_clean, re.IGNORECASE):
            return True

        # If it has digits, it's not pure watermark noise
        if any(c.isdigit() for c in s_clean):
            return False

        # Preserved statistical symbols are never noise
        if s_clean in ("-", "–", "—", "- ", "...", "…", "NA", "N/A", "na", "n/a", "%"):
            return False

        words = re.findall(r"[a-zA-Z]+", s_clean)
        if not words:
            # Only punctuation: e.g. '/ / :', '.', '..'
            return True

        # If all alphanumeric words are single letters (e.g. 'o g .', 's p', 'k a m e d / / :')
        if all(len(w) <= 1 for w in words):
            wm_char_set = set("https://demakkabbpsgoid")
            return set("".join(words).lower()).issubset(wm_char_set)

        return False

    @classmethod
    def clean_cell_text(cls, val: Any) -> str:
        """Removes internal newlines, watermark artifacts, and special noise from a cell."""
        if val is None:
            return ""
        s = str(val).strip()
        s = re.sub(r"\s+", " ", s)

        # 1. Preserve official BPS statistical symbols
        if s in ("-", "–", "—", "- ", "...", "…", "NA", "N/A", "na", "n/a", "%"):
            return s

        # 2. Check pure watermark noise
        if cls.is_watermark_noise(s):
            return ""

        # 3. Remove explicit watermark URL substrings
        s = re.sub(r"https?://[^\s]+", "", s, flags=re.IGNORECASE).strip()
        s = re.sub(r"demakkab\.bps\.go\.id", "", s, flags=re.IGNORECASE).strip()
        s = re.sub(r"\bd_i__o_g\b", "", s, flags=re.IGNORECASE).strip()

        # 4. Strip stray short noise letters prefixing a number: e.g. 'i . 82,3' -> '82,3', '. s p18,0' -> '18,0'
        m_pref = re.match(r"^[a-zA-Z\.\s/:]{1,6}\s*(-?\d+[\d\.,]*)$", s)
        if m_pref:
            s = m_pref.group(1).strip()

        # 5. Strip stray short noise letters suffixing a number: e.g. '82,3 o g .' -> '82,3'
        m_suff = re.match(r"^(-?\d+[\d\.,]*)\s*[a-zA-Z\.\s/:]{1,6}$", s)
        if m_suff:
            last_tok = s.split()[-1] if " " in s else ""
            if last_tok.lower() not in {"kg", "ton", "ha", "km", "m", "th"}:
                s = m_suff.group(1).strip()

        return re.sub(r"\s+", " ", s).strip()

    @classmethod
    def detect_header_rows(cls, raw_matrix: List[List[Any]], max_scan: int = 4) -> int:
        """
        Determines how many top rows constitute the multi-level header.
        """
        if not raw_matrix or len(raw_matrix) <= 1:
            return 1

        num_scan = min(len(raw_matrix) - 1, max_scan)
        header_depth = 1

        for r_idx in range(1, num_scan):
            row = raw_matrix[r_idx]
            cleaned_row = [cls.clean_cell_text(c) for c in row]
            
            num_numeric = sum(
                1 for c in cleaned_row 
                if re.match(r"^[\d\.,\-]+$", c) and len(c) > 0 and c != "-"
            )
            
            non_empty_count = sum(1 for c in cleaned_row if len(c) > 0)
            if non_empty_count > 0 and (num_numeric / non_empty_count) >= 0.5:
                break

            header_depth = r_idx + 1

        return header_depth

    @classmethod
    def flatten_multi_index_headers(
        cls, 
        header_rows: List[List[Any]]
    ) -> List[str]:
        """
        Flattens multi-row headers into clean single column names.
        """
        if not header_rows:
            return []
        
        num_cols = max(len(r) for r in header_rows)
        normalized_rows = []
        for row in header_rows:
            padded = list(row) + [""] * (num_cols - len(row))
            normalized_rows.append([cls.clean_cell_text(c) for c in padded])

        # Step 1: Forward-fill headers horizontally for merged top headers
        df_header = pd.DataFrame(normalized_rows)
        for r_idx in range(len(df_header)):
            curr_val = ""
            for c_idx in range(num_cols):
                val = df_header.iloc[r_idx, c_idx]
                if val:
                    if not re.match(r"^\(\d+\)$", val):
                        curr_val = val
                elif curr_val:
                    df_header.iloc[r_idx, c_idx] = curr_val

        # Step 2: Combine vertically
        final_headers: List[str] = []
        for c_idx in range(num_cols):
            col_parts: List[str] = []
            for r_idx in range(len(df_header)):
                val = df_header.iloc[r_idx, c_idx].strip()
                if not val or re.match(r"^\(\d+\)$", val):
                    continue
                if not col_parts or val.lower() != col_parts[-1].lower():
                    col_parts.append(val)

            if not col_parts:
                col_name = f"Kolom_{c_idx + 1}"
            else:
                col_name = "_".join(col_parts)

            col_name = col_name.replace("%", "Persen")
            col_name = re.sub(r"[^\w\s-]", "", col_name)
            col_name = re.sub(r"[\s-]+", "_", col_name).strip("_")
            final_headers.append(col_name)

        seen: Dict[str, int] = {}
        unique_headers: List[str] = []
        for h in final_headers:
            if not h:
                h = "Kolom"
            if h in seen:
                seen[h] += 1
                unique_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 1
                unique_headers.append(h)

        return unique_headers

    @classmethod
    def parse_statistical_cell(cls, val: Any) -> StatisticalCell:
        """
        Parses a statistical table cell preserving official BPS semantics,
        footnotes, revision indicators, and exact numerical types.
        """
        if val is None or pd.isna(val):
            return StatisticalCell(
                raw_value="",
                normalized_value=None,
                value_status=ValueStatus.NOT_AVAILABLE
            )

        raw_str = cls.clean_cell_text(val)
        if not raw_str:
            return StatisticalCell(
                raw_value="",
                normalized_value=None,
                value_status=ValueStatus.NOT_AVAILABLE
            )

        # 1. BPS Nil / Empty marker: '-' is NIL, NEVER 0
        if raw_str in ("-", "–", "—", "- "):
            return StatisticalCell(
                raw_value=raw_str,
                normalized_value=None,
                value_status=ValueStatus.NIL
            )

        # 2. Missing / Not available yet
        if raw_str in ("...", "…", "null", "NULL"):
            return StatisticalCell(
                raw_value=raw_str,
                normalized_value=None,
                value_status=ValueStatus.NOT_AVAILABLE
            )

        # 3. Not applicable
        if raw_str in ("NA", "N/A", "na", "n/a"):
            return StatisticalCell(
                raw_value=raw_str,
                normalized_value=None,
                value_status=ValueStatus.NOT_APPLICABLE
            )

        # 4. Negligible zero: '0,0' or '0,00'
        if raw_str in ("0,0", "0,00", "0.0", "0.00"):
            return StatisticalCell(
                raw_value=raw_str,
                normalized_value=0.0,
                value_status=ValueStatus.NEGLIGIBLE
            )

        # 5. Absolute zero
        if raw_str == "0":
            return StatisticalCell(
                raw_value=raw_str,
                normalized_value=0,
                value_status=ValueStatus.ZERO
            )

        # 6. Extract revision marks ('r', 'R') and footnotes ('*', '**')
        revision_mark = None
        footnote = None
        s_work = raw_str

        # Check revision suffix
        if re.search(r"(\s+|^|\d)r$", s_work, re.IGNORECASE):
            revision_mark = "r"
            s_work = re.sub(r"\s*r$", "", s_work, flags=re.IGNORECASE).strip()

        # Check asterisk footnote
        if "*" in s_work:
            footnote = "*" if "**" not in s_work else "**"
            s_work = s_work.replace("*", "").strip()

        # Check percentage
        unit = None
        if "%" in s_work:
            unit = "%"
            s_work = s_work.replace("%", "").strip()

        # Clean non-digit characters except dots, commas, and minus
        s_numeric = re.sub(r"[^\d\.,\-]", "", s_work).strip()

        # Case A: Indonesian format with thousand dots and comma decimal (e.g. 1.234.567,89)
        if re.match(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$", s_numeric):
            s_std = s_numeric.replace(".", "").replace(",", ".")
            try:
                f_val = float(s_std)
                norm_val = int(f_val) if f_val.is_integer() else f_val
                status = ValueStatus.REVISED if revision_mark else (ValueStatus.PROVISIONAL if footnote else ValueStatus.NORMAL_VALUE)
                return StatisticalCell(
                    raw_value=raw_str,
                    normalized_value=norm_val,
                    value_status=status,
                    unit=unit,
                    footnote=footnote,
                    revision_mark=revision_mark
                )
            except ValueError:
                pass

        # Case B: Standard Indonesian decimal (e.g. 123,45 or -5,2)
        elif re.match(r"^-?\d+(,\d+)$", s_numeric):
            s_std = s_numeric.replace(",", ".")
            try:
                f_val = float(s_std)
                norm_val = int(f_val) if f_val.is_integer() else f_val
                status = ValueStatus.REVISED if revision_mark else (ValueStatus.PROVISIONAL if footnote else ValueStatus.NORMAL_VALUE)
                return StatisticalCell(
                    raw_value=raw_str,
                    normalized_value=norm_val,
                    value_status=status,
                    unit=unit,
                    footnote=footnote,
                    revision_mark=revision_mark
                )
            except ValueError:
                pass

        # Case C: Plain integer or dot-decimal (e.g. 12345 or 123.45)
        elif re.match(r"^-?\d+(\.\d+)?$", s_numeric):
            try:
                f_val = float(s_numeric)
                norm_val = int(f_val) if f_val.is_integer() else f_val
                status = ValueStatus.REVISED if revision_mark else (ValueStatus.PROVISIONAL if footnote else ValueStatus.NORMAL_VALUE)
                return StatisticalCell(
                    raw_value=raw_str,
                    normalized_value=norm_val,
                    value_status=status,
                    unit=unit,
                    footnote=footnote,
                    revision_mark=revision_mark
                )
            except ValueError:
                pass

        # Textual / non-numeric cell
        return StatisticalCell(
            raw_value=raw_str,
            normalized_value=None,
            value_status=ValueStatus.TEXT,
            unit=unit,
            footnote=footnote,
            revision_mark=revision_mark
        )

    @classmethod
    def sanitize_indonesian_numeric(cls, val: Any) -> Any:
        """
        Backward-compatible sanitizer that uses parse_statistical_cell internally.
        Returns normalized number if available, None for NA/NIL, or raw cleaned string for text.
        """
        cell = cls.parse_statistical_cell(val)
        if cell.normalized_value is not None:
            return cell.normalized_value
        if cell.value_status in (ValueStatus.NIL, ValueStatus.NOT_AVAILABLE, ValueStatus.NOT_APPLICABLE):
            return None
        return cell.raw_value

    @classmethod
    def is_valid_statistical_table(cls, df: pd.DataFrame, title: str = "") -> bool:
        """
        Strict gatekeeper to ensure extracted matrix is a genuine BPS statistical table:
        1. Must have at least 2 rows and at least 2 columns.
        2. Title must not be a glossary definition (adalah, merupakan, etc.) or TOC entry.
        3. At least 35% of data cells must contain valid numbers or statistical symbols.
        """
        if df is None or df.empty:
            return False
        if len(df) < 2 or len(df.columns) < 2:
            return False

        t = (title or "").strip()
        # Reject glossary definitions
        if re.search(r"\b(adalah|merupakan|yaitu|diartikan|didefinisikan)\b", t, re.IGNORECASE):
            return False
        # Reject TOC leader dots
        if re.search(r"\.{3,}", t):
            return False
        # Reject narrative headings and preamble
        if re.search(r"^(daftar\s+(tabel|gambar|isi)|tim\s+penyusun|kata\s+pengantar|sistematika|bab\s+[\dIVXLCDM]+)", t, re.IGNORECASE):
            return False

        # Calculate numerical and statistical density in data cells
        total_cells = 0
        valid_stat_cells = 0
        for col in df.columns:
            for val in df[col]:
                if val is None or pd.isna(val) or val == "":
                    continue
                total_cells += 1
                cell = cls.parse_statistical_cell(val)
                if cell.normalized_value is not None or cell.value_status in (
                    ValueStatus.NIL, ValueStatus.NEGLIGIBLE, ValueStatus.ZERO,
                    ValueStatus.NOT_AVAILABLE, ValueStatus.NOT_APPLICABLE,
                    ValueStatus.PROVISIONAL, ValueStatus.REVISED
                ):
                    valid_stat_cells += 1

        if total_cells == 0:
            return False
        ratio = valid_stat_cells / total_cells
        return ratio >= 0.35

    @classmethod
    def clean_table_dataframe(
        cls, 
        raw_matrix: List[List[Any]], 
        header_depth: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Transforms raw extracted table matrix into a clean, structured pandas DataFrame:
        1. Expands embedded multiline rows (e.g. all desas merged in one cell).
        2. Multi-level header extraction & flattening.
        3. Contextual merged-cell forward-fill (respecting summary rows like Jumlah/Total).
        4. Statistical symbol parsing without destructive 0-coercion.
        """
        if isinstance(raw_matrix, pd.DataFrame):
            raw_matrix = [list(raw_matrix.columns)] + raw_matrix.values.tolist()
        if not raw_matrix or len(raw_matrix) < 2:
            return None

        if header_depth is None:
            header_depth = cls.detect_header_rows(raw_matrix)

        header_rows = raw_matrix[:header_depth]
        data_rows = raw_matrix[header_depth:]

        if not data_rows:
            return None

        headers = cls.flatten_multi_index_headers(header_rows)
        num_cols = len(headers)

        # Step 1: Expand embedded multiline rows (as observed in borderless tables)
        expanded_data_rows = []
        for r in data_rows:
            multilines = [str(c).strip().split("\n") for c in r if c is not None]
            max_lines = max((len(ml) for ml in multilines), default=1)
            
            if max_lines > 1:
                # If all columns have multiple lines matching row count
                if all(len(ml) == max_lines or len(ml) <= 1 for ml in multilines):
                    for l_idx in range(max_lines):
                        sub_row = []
                        for c in r:
                            c_lines = str(c).strip().split("\n") if c is not None else []
                            val = c_lines[l_idx].strip() if l_idx < len(c_lines) else (c_lines[0].strip() if len(c_lines) == 1 else "")
                            sub_row.append(val)
                        if any(sub_row):
                            expanded_data_rows.append(sub_row)
                else:
                    # One cell has all the lines (e.g. '1 Pilangwetan 558 2.395 4,29\n2 Kebonagung...')
                    for c in r:
                        if c is not None and "\n" in str(c):
                            for line in str(c).strip().split("\n"):
                                tokens = line.split()
                                if len(tokens) >= num_cols and num_cols > 1:
                                    cat = " ".join(tokens[:-(num_cols - 1)])
                                    vals = tokens[-(num_cols - 1):]
                                    expanded_data_rows.append([cat] + vals)
                                else:
                                    expanded_data_rows.append([line] + [""] * (num_cols - 1))
                            break
            else:
                expanded_data_rows.append(r)

        data_rows = expanded_data_rows

        normalized_data = []
        for r in data_rows:
            cleaned_r = [cls.clean_cell_text(c) for c in r]
            if len(cleaned_r) < num_cols:
                cleaned_r.extend([""] * (num_cols - len(cleaned_r)))
            elif len(cleaned_r) > num_cols:
                cleaned_r = cleaned_r[:num_cols]
            
            # Skip rows where all cells are empty or noise
            if any(cleaned_r) and not all(cls.is_watermark_noise(c) for c in cleaned_r if c):
                normalized_data.append(cleaned_r)

        if not normalized_data:
            return None

        df = pd.DataFrame(normalized_data, columns=headers)

        # Contextual forward-fill for category columns (leftmost 1 or 2 columns)
        summary_tokens = {"jumlah", "total", "rata-rata", "ratarata", "subtotal"}

        for col_idx in range(min(2, len(df.columns))):
            curr_val = ""
            for idx in range(len(df)):
                val = str(df.iloc[idx, col_idx]).strip() if df.iloc[idx, col_idx] is not None else ""
                row_str = " ".join(str(c).lower() for c in df.iloc[idx] if c is not None)
                is_summary = any(tok in row_str for tok in summary_tokens)
                
                if val:
                    curr_val = val
                elif not is_summary and curr_val:
                    df.iloc[idx, col_idx] = curr_val

        # Sanitize data cells using statistical notation parser
        for col in df.columns:
            df[col] = df[col].apply(cls.sanitize_indonesian_numeric)

        df = df.dropna(how="all", axis=1)
        return df
