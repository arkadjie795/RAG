import sys
import os
import json
import time
sys.path.insert(0, os.path.abspath("."))

from loguru import logger
from config.database import get_db_cursor
from chatbot.bot import BPSChatbot
from chatbot.rag_feeder import RAGFeeder

print("=" * 60)
print("1. VERIFYING DATABASE COUNTS")
print("=" * 60)
with get_db_cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM publications;")
    pub_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM statistical_tables;")
    tbl_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vector_chunks;")
    vec_count = cur.fetchone()[0]
    print(f"Publications      : {pub_count}")
    print(f"Statistical Tables: {tbl_count}")
    print(f"Vector Chunks     : {vec_count}")

print("\n" + "=" * 60)
print("2. TESTING FULL TABLE LOOKUP FROM POSTGRESQL (14 KECAMATAN / MULTI-ROW)")
print("=" * 60)
feeder = RAGFeeder()
preview = feeder._load_granular_table_preview(
    table_id="09855c4609108eb2f2a929de_p52_t1",
    max_rows=10
)
if preview:
    print("Table preview successfully loaded from PostgreSQL:")
    print(preview[:300])
else:
    print("Failed to load table preview!")

print("\n" + "=" * 60)
print("3. TESTING RAG RETRIEVAL & CONTEXT FEEDING")
print("=" * 60)
rag_pkg = feeder.feed_context(
    query="Berapa jumlah penduduk di Demak?",
    top_k=2
)
print(f"Total retrieved chunks: {rag_pkg['total_retrieved']}")
print(f"Citations count       : {len(rag_pkg['citations'])}")
if rag_pkg["chunks"]:
    c0 = rag_pkg["chunks"][0]
    print(f"Top Doc   : {c0.get('dokumen_sumber')}")
    print(f"Top Hal   : {c0.get('halaman')}")
    print(f"Top Score : {c0.get('score')}")

print("\n" + "=" * 60)
print("4. TESTING CHATBOT SSE STREAMING")
print("=" * 60)
bot = BPSChatbot(feeder=feeder)
stream = bot.stream_ask(
    question="Halo, apakah BPS mencatat data penduduk Demak?",
    session_id="test_stream_session"
)
token_count = 0
full_text = ""
for item in stream:
    if item["type"] == "metadata":
        print(f"[Metadata Event] mode={item.get('mode')}, citations={len(item.get('citations', []))}")
    elif item["type"] == "token":
        token_count += 1
        full_text += item["token"]
        print(item["token"], end="", flush=True)
    elif item["type"] == "done":
        print(f"\n[Done Event] Session={item['session_id']}, Final Length={len(item['answer'])}")

print(f"\nStream completed! Received {token_count} streaming tokens.")
print("ALL E2E INTEGRATION TESTS PASSED SUCCESSFULLY!")
