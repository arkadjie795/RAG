import pytest
from modules.storage.postgres_store import PostgresVectorStore

def test_postgres_vector_store_crud_and_search():
    store = PostgresVectorStore()
    mock_chunk = {
        "chunk_id": "test_chunk_sayung_001",
        "dokumen_id": "doc_demak_2024",
        "dokumen_sumber": "Kabupaten Demak Dalam Angka 2024",
        "daerah": "Sayung",
        "kategori": "Kependudukan",
        "tahun": "2024",
        "halaman": 45,
        "tipe_konten": "tabel_baris",
        "judul_tabel": "Jumlah Penduduk Menurut Kecamatan",
        "satuan": "Jiwa",
        "sumber": "BPS Kabupaten Demak",
        "representasi_teks": "Pada Kecamatan Sayung jumlah penduduk laki-laki adalah 54.120 Jiwa.",
        "embedding": [0.01] * 384
    }
    upserted = store.upsert_chunks([mock_chunk])
    assert upserted == 1

    results = store.search_with_prefilter(
        query_embedding=[0.01] * 384,
        daerah="Sayung",
        tahun="2024",
        n_results=1
    )
    assert len(results) >= 1
    assert results[0]["chunk_id"] == "test_chunk_sayung_001"
    assert "Sayung" in results[0]["representasi_teks"]
    assert results[0]["score"] is not None
