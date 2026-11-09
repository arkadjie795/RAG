import pytest
from modules.vectorization.embedder import VectorEmbedder

def test_embedder_caching_and_deterministic_storage():
    embedder = VectorEmbedder()
    test_texts = [
        "Jumlah Penduduk Kecamatan Sayung Tahun 2024",
        "Produksi Padi dan Luas Panen Kabupaten Demak"
    ]
    
    # First call computes and caches in PostgreSQL embedding_cache
    embs_1 = embedder.generate_embeddings(test_texts)
    assert len(embs_1) == 2
    assert len(embs_1[0]) == 384
    
    # Second call should fetch directly from cache with exact equality
    embs_2 = embedder.generate_embeddings(test_texts)
    assert len(embs_2) == 2
    assert embs_1[0] == embs_2[0]
    assert embs_1[1] == embs_2[1]

def test_embedder_never_returns_random_hash():
    embedder = VectorEmbedder()
    # Ensure the hazardous pseudo-random fallback method is completely eliminated
    assert not hasattr(embedder, "_generate_random_hash_vectors")
