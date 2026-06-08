from sentence_transformers import SentenceTransformer
from utils.db import get_db

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> list:
    """Convert text to a vector embedding"""
    return model.encode(text).tolist()

def semantic_search(query: str, limit: int = 3) -> list:
    """Find semantically similar past signal reports"""
    db = get_db()
    query_embedding = embed_text(query)
    
    results = db.signal_reports.aggregate([
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 20,
                "limit": limit
            }
        },
        {
            "$project": {
                "match_result": 1,
                "created_at": 1,
                "signals": 1,
                "score": {"$meta": "vectorSearchScore"},
                "_id": 0
            }
        }
    ])
    
    return list(results)

if __name__ == "__main__":
    print("🔍 Testing vector search...")
    results = semantic_search("South American team winning a final")
    if results:
        for r in results:
            print(f"  Match: {r.get('match_result', 'N/A')} | Score: {r.get('score', 0):.3f}")
    else:
        print("  No results — reports may not have embeddings yet. Run the app and analyze a match first.")