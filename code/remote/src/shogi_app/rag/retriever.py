from typing import Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer


def retrieve_relevant_documents(
    query: str,
    collection_name: str = "positions",
    n_results: int = 5,
    chroma_client: Optional[chromadb.Client] = None,
    embedding_model: Optional[SentenceTransformer] = None,
) -> List[Dict]:
    """ChromaDBから関連ドキュメントを取得

    Args:
        query: クエリテキスト
        collection_name: コレクション名
        n_results: 取得するドキュメント数
        chroma_client: ChromaDBクライアント（オプション）
        embedding_model: Embeddingモデル（オプション）

    Returns:
        関連ドキュメントリスト
    """
    if chroma_client is None:
        chroma_client = chromadb.PersistentClient(
            path="/tmp/shogi/chromadb",
        )

    if embedding_model is None:
        embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    query_embedding = embedding_model.encode(query).tolist()

    try:
        collection = chroma_client.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        documents = []
        for i in range(len(results["documents"][0])):
            documents.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return documents
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []
