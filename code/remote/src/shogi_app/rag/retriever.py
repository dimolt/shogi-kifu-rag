from shogi_app.vector.chromadb_service import ChromadbService


def retrieve_relevant_documents(
    query: str,
    collection_name: str = 'positions',
    n_results: int = 5,
) -> list[dict]:
    """ChromaDBから関連ドキュメントを取得する。

    ChromadbService のシングルトンを通じてクライアントとモデルを取得する。

    Args:
        query: クエリテキスト。
        collection_name: 検索対象のコレクション名。
        n_results: 取得するドキュメント数。

    Returns:
        関連ドキュメントのリスト。各要素は text / metadata / distance キーを持つ辞書。
        取得に失敗した場合は空リストを返す。
    """
    service = ChromadbService.get_instance()
    service.ensure()

    query_embedding = service.encode_query(query)

    try:
        collection = service.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        documents = []
        for i in range(len(results['documents'][0])):
            documents.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
            })
        return documents
    except Exception as e:
        # コレクションが存在しない・空などの場合は空リストで続行
        print(f'Retrieval error: {e}')
        return []
