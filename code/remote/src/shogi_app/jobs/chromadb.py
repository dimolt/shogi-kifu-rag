import chromadb
from pyspark.sql import SparkSession
from sentence_transformers import SentenceTransformer


def collection_exists(chroma_client, name: str) -> bool:
    """Collectionの存在確認

    Args:
        chroma_client: ChromaDBクライアント
        name: コレクション名

    Returns:
        Collectionが存在する場合はTrue
    """
    try:
        chroma_client.get_collection(name)
        return True
    except Exception:
        return False


def clean_position_features(df):
    df["search_text"] = df["search_text"].astype(str).str.strip()

    return df[
        df["search_text"].notna() &
        (df["search_text"] != "") &
        (df["search_text"].str.lower() != "nan")
    ]


def rebuild_positions(chroma_client, embedding_model, spark):
    """positionsコレクションを再構築

    Args:
        chroma_client: ChromaDBクライアント
        embedding_model: Embeddingモデル
        spark: SparkSession
    """
    # positionsコレクションの削除と作成
    try:
        chroma_client.delete_collection("positions")
    except Exception:
        pass

    positions_collection = chroma_client.create_collection(
        name="positions",
        metadata={"hnsw:space": "cosine"},
    )

    # Gold Tableからposition_featuresを読み込み
    position_features_df = spark.table("shogi.shogi_gold.position_features").toPandas()
    position_features_df = clean_position_features(position_features_df)

    # positionsコレクションにデータを追加
    if len(position_features_df) > 0:
        texts = position_features_df["search_text"].tolist()

        if len(texts) == 0:
            print("No valid texts for embedding. Skip embedding step.")
            embeddings = []
        else:
            embeddings = embedding_model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False
            ).tolist()

        if len(texts) > 0:
            positions_collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=[{
                    "game_id": str(row["game_id"]),
                    "move_number": int(row["move_number"]),
                    "sfen": str(row["sfen"]),
                    "move_usi": str(row["move_usi"]),
                    "player": str(row["player"]),
                    "move_quality": str(row["move_quality"]),
                    "score_cp": int(row["score_cp"]),
                } for _, row in position_features_df.iterrows()],
                ids=[f"pos_{i}" for i in range(len(position_features_df))],
            )
        else:
            print("Skip Chroma insert because no valid data")


def rebuild_floodgate(chroma_client, embedding_model, spark):
    """floodgate_positionsコレクションを再構築

    Args:
        chroma_client: ChromaDBクライアント
        embedding_model: Embeddingモデル
        spark: SparkSession
    """
    # Silver Tableからfloodgate_positionsを読み込み
    try:
        floodgate_df = spark.table("shogi.shogi_silver.floodgate_positions").toPandas()
    except Exception:
        floodgate_df = None

    # floodgate_positionsコレクションの削除と作成
    if floodgate_df is not None and len(floodgate_df) > 0:
        try:
            chroma_client.delete_collection("floodgate_positions")
        except Exception:
            pass

        floodgate_collection = chroma_client.create_collection(
            name="floodgate_positions",
            metadata={"hnsw:space": "cosine"},
        )

        # floodgate_positionsコレクションにデータを追加
        search_texts = [
            f"局面: {row['sfen']} 指し手: {row['move_usi']}"
            for _, row in floodgate_df.iterrows()
        ]
        embeddings = embedding_model.encode(search_texts).tolist()
        floodgate_collection.add(
            embeddings=embeddings,
            documents=search_texts,
            metadatas=[{
                "game_id": str(row["game_id"]),
                "move_number": int(row["move_number"]),
                "sfen": str(row["sfen"]),
                "move_usi": str(row["move_usi"]),
                "player": str(row["player"]),
            } for _, row in floodgate_df.iterrows()],
            ids=[f"floodgate_{i}" for i in range(len(floodgate_df))],
        )


def rebuild_joseki(chroma_client, embedding_model, spark):
    """joseki_knowledgeコレクションを再構築

    Args:
        chroma_client: ChromaDBクライアント
        embedding_model: Embeddingモデル
        spark: SparkSession
    """
    # Silver Tableからjoseki_knowledgeを読み込み
    try:
        joseki_df = spark.table("shogi.shogi_silver.joseki_knowledge").toPandas()
    except Exception:
        joseki_df = None

    # joseki_knowledgeコレクションの削除と作成
    if joseki_df is not None and len(joseki_df) > 0:
        try:
            chroma_client.delete_collection("joseki_knowledge")
        except Exception:
            pass
        joseki_collection = chroma_client.create_collection(
            name="joseki_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

        # joseki_knowledgeコレクションにデータを追加
        embeddings = embedding_model.encode(joseki_df["content"].tolist()).tolist()
        joseki_collection.add(
            embeddings=embeddings,
            documents=joseki_df["content"].tolist(),
            metadatas=[{
                "strategy": str(row["strategy"]),
                "source": str(row["source"]),
            } for _, row in joseki_df.iterrows()],
            ids=[f"joseki_{i}" for i in range(len(joseki_df))],
        )


def main():
    spark = SparkSession.getActiveSession()

    # Embeddingモデルの初期化
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # ChromaDBの初期化
    chroma_client = chromadb.PersistentClient(
        path="/tmp/shogi/chromadb",
    )

    rebuild_positions(chroma_client, embedding_model, spark)
    rebuild_floodgate(chroma_client, embedding_model, spark)
    rebuild_joseki(chroma_client, embedding_model, spark)
