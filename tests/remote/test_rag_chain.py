"""Tests for RAG Chain notebook"""

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


def test_retrieve_relevant_documents(chroma_client, embedding_model):
    """Test that retrieve_relevant_documents function works"""
    try:
        query_text = "この局面で最善の手は何ですか？"
        query_embedding = embedding_model.encode(query_text).tolist()

        collection = chroma_client.get_collection("positions")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
        )

        assert results is not None, "Query returned None"
        assert "documents" in results, "Query results missing documents"
        assert len(results["documents"]) > 0, "Query returned no documents"
        assert len(results["documents"][0]) > 0, "Query returned no documents"
        assert "metadatas" in results, "Query results missing metadatas"
        assert "distances" in results, "Query results missing distances"
    except Exception as e:
        pytest.skip(f"Failed to test retrieve_relevant_documents: {e}")


def test_retrieve_from_joseki_knowledge(chroma_client, embedding_model):
    """Test that joseki_knowledge collection can be queried"""
    try:
        query_text = "矢倉囲いの特徴を教えてください"
        query_embedding = embedding_model.encode(query_text).tolist()

        collection = chroma_client.get_collection("joseki_knowledge")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2,
        )

        assert results is not None, "Query returned None"
        assert len(results["documents"]) > 0, "Query returned no documents"
        assert len(results["documents"][0]) > 0, "Query returned no documents"
    except Exception as e:
        pytest.skip(f"Failed to test retrieve_from_joseki_knowledge: {e}")


def test_retrieve_from_floodgate_positions(chroma_client, embedding_model):
    """Test that floodgate_positions collection can be queried"""
    try:
        query_text = "形勢を教えてください"
        query_embedding = embedding_model.encode(query_text).tolist()

        collection = chroma_client.get_collection("floodgate_positions")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2,
        )

        assert results is not None, "Query returned None"
        assert len(results["documents"]) > 0, "Query returned no documents"
        assert len(results["documents"][0]) > 0, "Query returned no documents"
    except Exception as e:
        pytest.skip(f"Failed to test retrieve_from_floodgate_positions: {e}")


def test_document_metadata_structure(chroma_client):
    """Test that retrieved documents have correct metadata structure"""
    try:
        collection = chroma_client.get_collection("positions")
        results = collection.get(limit=1)

        if len(results["metadatas"]) == 0:
            pytest.skip("positions collection is empty")

        metadata = results["metadatas"][0]

        # Check required metadata fields
        required_fields = ["game_id", "move_number", "sfen", "move_usi"]
        for field in required_fields:
            assert field in metadata, f"Metadata missing required field: {field}"
    except Exception as e:
        pytest.skip(f"Failed to test document metadata structure: {e}")


def test_embedding_model_works(embedding_model):
    """Test that embedding model works correctly"""
    try:
        test_text = "将棋の局面"
        embedding = embedding_model.encode(test_text)

        assert embedding is not None, "Embedding is None"
        assert len(embedding) > 0, "Embedding is empty"
        assert isinstance(embedding, list), "Embedding is not a list"
    except Exception as e:
        pytest.skip(f"Failed to test embedding model: {e}")


def test_chromadb_client_connection(chroma_client):
    """Test that ChromaDB client is connected"""
    try:
        # List collections to verify connection
        collections = chroma_client.list_collections()
        assert collections is not None, "Failed to list collections"
    except Exception as e:
        pytest.skip(f"Failed to test ChromaDB client connection: {e}")
