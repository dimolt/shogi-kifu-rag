"""ChromaDB Vector Store

Gold TableとSilver TableからChromaDB Vector Storeを構築するノートブック
"""

from pyspark.sql import SparkSession
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os

# SparkSessionの初期化
spark = SparkSession.builder.getOrCreate()

# ChromaDBの初期化
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="/tmp/shogi/chromadb",
))

# Embeddingモデルの初期化
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Gold Tableからposition_featuresを読み込み
position_features_df = spark.table("shogi.shogi_gold.position_features").toPandas()

# positionsコレクションの作成
try:
    chroma_client.delete_collection("positions")
except:
    pass

positions_collection = chroma_client.create_collection(
    name="positions",
    metadata={"hnsw:space": "cosine"},
)

# positionsコレクションにデータを追加
if len(position_features_df) > 0:
    embeddings = embedding_model.encode(position_features_df["search_text"].tolist()).tolist()
    positions_collection.add(
        embeddings=embeddings,
        documents=position_features_df["search_text"].tolist(),
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

# Silver Tableからfloodgate_positionsを読み込み
try:
    floodgate_df = spark.table("shogi.shogi_silver.floodgate_positions").toPandas()
except:
    floodgate_df = None

# floodgate_positionsコレクションの作成
if floodgate_df is not None and len(floodgate_df) > 0:
    try:
        chroma_client.delete_collection("floodgate_positions")
    except:
        pass

    floodgate_collection = chroma_client.create_collection(
        name="floodgate_positions",
        metadata={"hnsw:space": "cosine"},
    )

    # floodgate_positionsコレクションにデータを追加
    search_texts = [f"局面: {row['sfen']} 指し手: {row['move_usi']}" for _, row in floodgate_df.iterrows()]
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

# Silver Tableからjoseki_knowledgeを読み込み
try:
    joseki_df = spark.table("shogi.shogi_silver.joseki_knowledge").toPandas()
except:
    joseki_df = None

# joseki_knowledgeコレクションの作成
if joseki_df is not None and len(joseki_df) > 0:
    try:
        chroma_client.delete_collection("joseki_knowledge")
    except:
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
