import pytest
from modules.retrieval.entity_dictionary import DemakEntityExtractor
from modules.retrieval.hybrid_search import HybridRetriever

def test_demak_entity_extraction():
    extractor = DemakEntityExtractor()
    ent = extractor.extract_entities("Berapa luas wilayah di kec Mranggen tahun 2024?")
    assert ent["kecamatan"] == "Mranggen"
    assert ent["tahun"] == "2024"

    # Test alias and lowercase
    ent2 = extractor.extract_entities("Jumlah penduduk karang tengah thn 2023")
    assert ent2["kecamatan"] == "Karangtengah"
    assert ent2["tahun"] == "2023"

def test_hybrid_search_rrf_execution():
    retriever = HybridRetriever()
    results = retriever.search("Jumlah penduduk Kecamatan Sayung tahun 2024", top_k=3)
    assert isinstance(results, list)
    if results:
        assert "score" in results[0]
        assert "representasi_teks" in results[0]
