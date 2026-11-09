import pytest
from modules.extraction.table_cleaner import TableCleaner, StatisticalCell, ValueStatus

def test_statistical_symbol_semantics():
    # Dash should NOT be integer 0; should be NIL
    cell_dash = TableCleaner.parse_statistical_cell("-")
    assert cell_dash.value_status == ValueStatus.NIL
    assert cell_dash.raw_value == "-"
    assert cell_dash.normalized_value is None

    # Ellipsis should be NOT_AVAILABLE
    cell_el = TableCleaner.parse_statistical_cell("...")
    assert cell_el.value_status == ValueStatus.NOT_AVAILABLE
    assert cell_el.normalized_value is None

    # Absolute zero
    cell_zero = TableCleaner.parse_statistical_cell("0")
    assert cell_zero.value_status == ValueStatus.ZERO
    assert cell_zero.normalized_value == 0

    # Revision and footnote indicators preserved
    cell_rev = TableCleaner.parse_statistical_cell("12.450 r")
    assert cell_rev.value_status == ValueStatus.REVISED
    assert cell_rev.normalized_value == 12450
    assert cell_rev.revision_mark == "r"

    cell_prov = TableCleaner.parse_statistical_cell("5.120*")
    assert cell_prov.value_status == ValueStatus.PROVISIONAL
    assert cell_prov.normalized_value == 5120
    assert cell_prov.footnote == "*"

    # Indonesian float parsing: dot thousand, comma decimal
    cell_float = TableCleaner.parse_statistical_cell("1.234,50")
    assert cell_float.normalized_value == 1234.50

    cell_float_millions = TableCleaner.parse_statistical_cell("1.234.567,89")
    assert cell_float_millions.normalized_value == 1234567.89

def test_clean_table_dataframe_preserves_semantics():
    raw_matrix = [
        ["Kecamatan", "Kategori Usia", "Jumlah"],
        ["Mranggen", "0-14 Tahun", "15.000"],
        ["", "15-64 Tahun", "35.000"],
        ["Sayung", "0-14 Tahun", "12.000"],
        ["", "15-64 Tahun", "-"]
    ]
    df = TableCleaner.clean_table_dataframe(raw_matrix, header_depth=1)
    assert df is not None
    assert len(df) == 4
    # Column Kecamatan should be forward-filled properly for sub-rows
    assert df["Kecamatan"].tolist() == ["Mranggen", "Mranggen", "Sayung", "Sayung"]
    # The last cell was '-' so it should NOT be 0, but NaN/None NIL representation
    import pandas as pd
    assert pd.isna(df["Jumlah"].iloc[3])
    assert df["Jumlah"].iloc[3] != 0
