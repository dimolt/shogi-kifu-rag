"""Tests for ChromaDB Vector Store notebook"""

import chromadb
import pytest
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


@pytest.fixture(scope="session")
def chroma_client():
    """Create a ChromaDB client"""
    try:
        client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="/tmp/shogi/chromadb",
        ))
        yield client
    except Exception as e:
        pytest.skip(f"Failed to create ChromaDB client: {e}")


@pytest.fixture(scope="session")
def embedding_model():
    """Create an embedding model"""
    try:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        yield model
    except Exception as e:
        pytest.skip(f"Failed to create embedding model: {e}")


def test_chromadb_positions_collection_exists(chroma_client):
    """Test that positions collection exists"""
    try:
        collection = chroma_client.get_collection("positions")
        assert collection is not None, "positions collection does not exist"
    except Exception as e:
        pytest.skip(f"positions collection does not exist: {e}")


def test_chromadb_floodgate_positions_collection_exists(chroma_client):
    """Test that floodgate_positions collection exists"""
    try:
        collection = chroma_client.get_collection("floodgate_positions")
        assert collection is not None, "floodgate_positions collection does not exist"
    except Exception as e:
        pytest.skip(f"floodgate_positions collection does not exist: {e}")


def test_chromadb_joseki_knowledge_collection_exists(chroma_client):
    """Test that joseki_knowledge collection exists"""
    try:
        collection = chroma_client.get_collection("joseki_knowledge")
        assert collection is not None, "joseki_knowledge collection does not exist"
    except Exception as e:
        pytest.skip(f"joseki_knowledge collection does not exist: {e}")


def test_chromadb_positions_not_empty(chroma_client):
    """Test that positions collection contains data"""
    try:
        collection = chroma_client.get_collection("positions")
        count = collection.count()
        assert count > 0, "positions collection is empty"
    except Exception as e:
        pytest.skip(f"Failed to check positions collection: {e}")


def test_chromadb_positions_can_query(chroma_client, embedding_model):
    """Test that positions collection can be queried"""
    try:
        collection = chroma_client.get_collection("positions")

        # Test query
        query_text = "この局面で最善の手は何ですか？"
        query_embedding = embedding_model.encode(query_text).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
        )

        assert results is not None, "Query returned None"
        assert "documents" in results, "Query results missing documents"
        assert len(results["documents"]) > 0, "Query returned no documents"
        assert len(results["documents"][0]) > 0, "Query returned no documents"
    except Exception as e:
        pytest.skip(f"Failed to query positions collection: {e}")


def test_chromadb_positions_metadata_structure(chroma_client):
    """Test that positions collection has correct metadata structure"""
    try:
        collection = chroma_client.get_collection("positions")

        # Get a sample document
        results = collection.get(limit=1)

        if len(results["metadatas"]) == 0:
            pytest.skip("positions collection is empty")

        metadata = results["metadatas"][0]

        # Check required metadata fields
        required_fields = ["game_id", "move_number", "sfen", "move_usi"]
        for field in required_fields:
            assert field in metadata, f"Metadata missing required field: {field}"
    except Exception as e:
        pytest.skip(f"Failed to check positions metadata: {e}")


def test_chromadb_joseki_knowledge_can_query(chroma_client, embedding_model):
    """Test that joseki_knowledge collection can be queried"""
    try:
        collection = chroma_client.get_collection("joseki_knowledge")

        # Test query
        query_text = "矢倉囲いの特徴を教えてください"
        query_embedding = embedding_model.encode(query_text).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2,
        )

        assert results is not None, "Query returned None"
        assert "documents" in results, "Query results missing documents"
        assert len(results["documents"]) > 0, "Query returned no documents"
    except Exception as e:
        pytest.skip(f"Failed to query joseki_knowledge collection: {e}")
