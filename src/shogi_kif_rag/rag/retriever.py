from shogi_kif_rag.vector import SearchIndex


def retrieve_relevant_documents(
    search_index: SearchIndex,
    query: str,
    n_results: int = 5,
) -> list[dict]:
    """SearchIndexから関連ドキュメントを取得する。

    SearchIndex共通インターフェースを通じて検索を行う。

    Args:
        search_index: SearchIndex インスタンス。
        query: クエリテキスト。
        n_results: 取得するドキュメント数。

    Returns:
        関連ドキュメントのリスト。各要素は text / metadata / score キーを持つ辞書。
        取得に失敗した場合は空リストを返す。
    """
    try:
        search_results = search_index.search(query, top_k=n_results)
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
