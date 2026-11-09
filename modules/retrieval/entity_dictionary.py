"""
Master Geographic and Statistical Entity Dictionary for Kabupaten Demak (Code: 3321).
Extracts kecamatan, reference years, indicators, and handles common typing variants.
"""
import re
from typing import Dict, Any, Optional, List


class DemakEntityExtractor:
    """Extracts geographic entities and temporal markers for Kabupaten Demak."""

    KECAMATAN_MAP = {
        "mranggen": "Mranggen",
        "sayung": "Sayung",
        "karangawen": "Karangawen",
        "guntur": "Guntur",
        "bonang": "Bonang",
        "wedung": "Wedung",
        "mijen": "Mijen",
        "gajah": "Gajah",
        "karanganyar": "Karanganyar",
        "karang tengah": "Karangtengah",
        "karangtengah": "Karangtengah",
        "wonosalam": "Wonosalam",
        "dempet": "Dempet",
        "kebonagung": "Kebonagung",
        "demak": "Demak"
    }

    def __init__(self):
        # Order keys by length descending to match 'karang tengah' before 'karang'
        self.sorted_kec_keys = sorted(self.KECAMATAN_MAP.keys(), key=len, reverse=True)

    def extract_entities(self, query: str) -> Dict[str, Optional[str]]:
        """
        Parses query to extract kecamatan, reference year, and query topics.
        """
        q_lower = query.lower()
        # Clean punctuation for exact word boundary checks
        q_clean = re.sub(r"[^\w\s]", " ", q_lower)

        # 1. Extract Kecamatan
        matched_kec = None
        for key in self.sorted_kec_keys:
            # Check standalone word or phrase
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, q_clean):
                matched_kec = self.KECAMATAN_MAP[key]
                break

        # 2. Extract Reference Year (4 digits from 2010 to 2029)
        matched_year = None
        year_match = re.search(r"\b(201[0-9]|202[0-9])\b", query)
        if year_match:
            matched_year = year_match.group(1)

        # 3. Detect category / indicator hints
        kategori_hint = None
        if any(w in q_clean for w in ["penduduk", "jiwa", "kelahiran", "kematian", "sex ratio"]):
            kategori_hint = "Kependudukan"
        elif any(w in q_clean for w in ["padi", "panen", "beras", "jagung", "pertanian", "tani"]):
            kategori_hint = "Pertanian"
        elif any(w in q_clean for w in ["pdrb", "ekonomi", "inflasi", "ihk"]):
            kategori_hint = "Ekonomi"
        elif any(w in q_clean for w in ["ikan", "tambak", "nelayan", "perikanan", "udang", "bandeng"]):
            kategori_hint = "Perikanan"
        elif any(w in q_clean for w in ["sekolah", "murid", "guru", "pendidikan"]):
            kategori_hint = "Sosial"

        return {
            "kecamatan": matched_kec,
            "tahun": matched_year,
            "kategori": kategori_hint,
            "daerah": matched_kec or "Kabupaten Demak"
        }


# Official list of 14 Kecamatan in Kabupaten Demak
DEMAK_KECAMATAN: List[str] = sorted(list(set(DemakEntityExtractor.KECAMATAN_MAP.values())))

