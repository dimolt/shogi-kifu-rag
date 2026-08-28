
from shogi_kif_rag.vector.base import SearchIndex

from .generator import generate_response
from .llm_client import LLMClient
from .retriever import retrieve_relevant_documents


def rag_query(
    search_index: SearchIndex,
    query: str,
    n_results: int = 5,
    llm_client=None,
) -> dict:
    """RAGクエリを実行

    Args:
        search_index: SearchIndex インスタンス
        query: クエリテキスト
        n_results: 取得するドキュメント数
        llm_client: LLMクライアント（オプション）

    Returns:
        RAG結果（回答と参照ドキュメント）
    """
    if llm_client is None:
        llm_client = LLMClient()

    documents = retrieve_relevant_documents(
        search_index, query, n_results
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
