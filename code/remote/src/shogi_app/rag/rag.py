from typing import Dict, List

from .generator import generate_response
from .llm_client import LLMClient
from .retriever import retrieve_relevant_documents


def rag_query(
    query: str,
    collection_name: str = "positions",
    n_results: int = 5,
    chroma_client=None,
    embedding_model=None,
    llm_client=None,
) -> Dict:
    """RAGクエリを実行

    Args:
        query: クエリテキスト
        collection_name: コレクション名
        n_results: 取得するドキュメント数
        chroma_client: ChromaDBクライアント（オプション）
        embedding_model: Embeddingモデル（オプション）
        llm_client: LLMクライアント（オプション）

    Returns:
        RAG結果（回答と参照ドキュメント）
    """
    if llm_client is None:
        llm_client = LLMClient()

    documents = retrieve_relevant_documents(
        query, collection_name, n_results, chroma_client, embedding_model
    )
    if not documents:
        return {
            "answer": "関連する情報が見つかりませんでした。",
            "documents": [],
        }
    answer = generate_response(query, documents, llm_client)
    return {
        "answer": answer,
        "documents": documents,
    }
