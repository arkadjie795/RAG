import sqlite3

conn = sqlite3.connect('database/chroma_store/chroma.sqlite3')
cur = conn.cursor()
cur.execute("SELECT DISTINCT string_value FROM embedding_metadata WHERE key = 'dokumen_id' LIMIT 20;")
docs = [r[0] for r in cur.fetchall()]
print('Distinct dokumen_id in Chroma metadata (sample 20):', docs)

cur.execute("SELECT COUNT(DISTINCT string_value) FROM embedding_metadata WHERE key = 'dokumen_id';")
total_docs = cur.fetchone()[0]
print('Total distinct dokumen_id in Chroma metadata:', total_docs)
conn.close()
