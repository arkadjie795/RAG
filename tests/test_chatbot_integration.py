import pytest
from chatbot.bot import BPSChatbot
from chatbot.rag_feeder import RAGFeeder

def test_chatbot_grounded_answer_pipeline():
    bot = BPSChatbot(warmup_background=False)
    # 1. Test conversational greeting bypass
    resp_greet = bot.ask("Halo, selamat pagi!", session_id="test_sess_01")
    assert resp_greet["type"] == "conversational"
    assert resp_greet["answer"] is not None

def test_rag_feeder_hybrid_retrieval_routing():
    feeder = RAGFeeder()
    # 2. Test feed_context routing to PostgreSQL HybridRetriever
    context_pkg = feeder.feed_context("Berapa jumlah penduduk di Kecamatan Sayung?")
    assert "context_text" in context_pkg
    assert "citations" in context_pkg
    assert isinstance(context_pkg["citations"], list)
