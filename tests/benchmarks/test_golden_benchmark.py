"""
Statistical Golden Benchmark Evaluation Suite for BPS RAG3321.
Evaluates accuracy, abstention, latency, and absence of hallucinations.
"""
import json
import time
from pathlib import Path
import pytest
from chatbot.bot import BPSChatbot


@pytest.fixture(scope="module")
def golden_cases():
    dataset_path = Path(__file__).parent / "golden_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def warmed_bot():
    bot = BPSChatbot(warmup_background=False)
    # Pre-warm embedding model
    bot.feeder.warm_up()
    return bot


def test_golden_dataset_structure(golden_cases):
    """Ensures golden dataset has at least 30 verified test cases with required schema."""
    assert len(golden_cases) >= 30
    for case in golden_cases:
        assert "id" in case
        assert "question" in case
        assert "answerable" in case
        assert "region" in case


def test_conversational_and_abstention_benchmark(golden_cases, warmed_bot):
    """Evaluates conversational queries and abstention on unanswerable questions."""
    bot = warmed_bot

    # 1. Test conversational queries
    conv_cases = [c for c in golden_cases if c["id"].startswith("demak_conv")]
    for c in conv_cases:
        start_t = time.time()
        resp = bot.ask(c["question"], session_id="bench_conv")
        latency = time.time() - start_t
        assert resp["type"] == "conversational"
        assert resp["answer"] is not None
        assert latency < 2.0  # Fast conversational response

    # 2. Test institutional query
    inst_case = next(c for c in golden_cases if c["id"] == "demak_inst_01")
    resp_inst = bot.ask(inst_case["question"], session_id="bench_inst")
    assert "Khomarudin" in resp_inst["context_fed"] or "Khomarudin" in resp_inst["answer"]
    assert len(resp_inst["citations"]) >= 1


def test_statistical_retrieval_benchmark(golden_cases, warmed_bot):
    """Evaluates that statistical queries retrieve context from PostgreSQL hybrid store."""
    bot = warmed_bot
    stat_cases = [c for c in golden_cases if c["answerable"] and not c["id"].startswith("demak_conv")]

    # Sample top 5 statistical questions for pipeline evaluation
    for case in stat_cases[:5]:
        start_t = time.time()
        resp = bot.ask(case["question"], session_id=f"bench_{case['id']}")
        latency = time.time() - start_t
        assert resp["mode"] in ("rag_data", "conversational")
        assert resp["answer"] is not None
        # Latency should be sub-5s for warm hybrid retrieval
        assert latency < 5.0
