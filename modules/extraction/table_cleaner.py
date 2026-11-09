"""
Table Cleaner Module for BPS Statistical Tables.
Handles multi-index header flattening, contextual forward fill, and Indonesian BPS statistical symbol preservation.
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
    def clean_cell_text(val: Any) -> str:
        """Removes internal newlines, extra spaces, and special artifacts from a cell."""
        if val is None:
            return ""
        s = str(val).strip()
        s = re.sub(r"\s+", " ", s)
        return s

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
        if raw_str in ("NA", "N/A", "n/a", "na"):
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
    def clean_table_dataframe(
        cls, 
        raw_matrix: List[List[Any]], 
        header_depth: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Transforms raw extracted table matrix into a clean, structured pandas DataFrame:
        1. Multi-level header extraction & flattening
        2. Contextual merged-cell forward-fill (respecting summary rows like Jumlah/Total)
        3. Statistical symbol parsing without destructive 0-coercion
        """
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

        normalized_data = []
        for r in data_rows:
            cleaned_r = [cls.clean_cell_text(c) for c in r]
            if len(cleaned_r) < num_cols:
                cleaned_r.extend([""] * (num_cols - len(cleaned_r)))
            elif len(cleaned_r) > num_cols:
                cleaned_r = cleaned_r[:num_cols]
            
            if any(cleaned_r):
                normalized_data.append(cleaned_r)

        if not normalized_data:
            return None

        df = pd.DataFrame(normalized_data, columns=headers)

        # Contextual forward-fill for category columns (leftmost 1 or 2 columns)
        # Summary keywords that must NOT be forward-filled over
        summary_tokens = {"jumlah", "total", "rata-rata", "ratarata", "subtotal"}

        for col_idx in range(min(2, len(df.columns))):
            col_name = df.columns[col_idx]
            curr_val = ""
            for idx in range(len(df)):
                val = df.iloc[idx, col_idx].strip()
                # Check if this row is a summary row
                row_str = " ".join(str(c).lower() for c in df.iloc[idx])
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
