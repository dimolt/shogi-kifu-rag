from shogi_kif_rag.vector import VectorStore


def retrieve_relevant_documents(
    vector_store: VectorStore,
    query: str,
    n_results: int = 5,
) -> list[dict]:
    """VectorStoreから関連ドキュメントを取得する。

    VectorStore共通インターフェースを通じて検索を行う。

    Args:
        vector_store: VectorStore インスタンス。
        query: クエリテキスト。
        n_results: 取得するドキュメント数。

    Returns:
        関連ドキュメントのリスト。各要素は text / metadata / score キーを持つ辞書。
        取得に失敗した場合は空リストを返す。
    """
    try:
        search_results = vector_store.search(query, top_k=n_results)
        documents = []
        for result in search_results:
            documents.append({
                'text': result['document']['text'],
                'metadata': result['document']['metadata'],
                'score': result['score'],
            })
        return documents
    except Exception as e:
        # 検索が失敗した場合は空リストで続行
        print(f'Retrieval error: {e}')
        return []
