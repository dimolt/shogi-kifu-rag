# Databricks Connect Integration Tests

This directory contains integration tests for remote Databricks notebooks using Databricks Connect.

## Prerequisites

- Databricks Workspace with a running cluster
- Databricks Connect configured with credentials
- Python 3.12+ with required dependencies

## Setup

1. Install dependencies:
```powershell
.\scripts\sync-env.ps1 remote
```

2. Set environment variables:
```powershell
$env:DATABRICKS_HOST = "https://your-workspace.cloud.databricks.com"
$env:DATABRICKS_TOKEN = "your-token"
$env:DATABRICKS_CLUSTER_ID = "your-cluster-id"
```

## Running Tests

Run all integration tests:
```powershell
pytest tests/remote/ -v
```

Run specific test file:
```powershell
pytest tests/remote/test_silver_table.py -v
```

Run specific test:
```powershell
pytest tests/remote/test_silver_table.py::test_silver_table_schema -v
```

## Test Coverage

- `test_silver_table.py`: Silver Table registration tests
- `test_gold_table.py`: Gold Table construction tests
- `test_chromadb.py`: ChromaDB Vector Store tests
- `test_rag_chain.py`: RAG Chain tests

## Notes

- Tests will be skipped if Databricks Connect credentials are not set
- Tests will be skipped if required tables/collections do not exist
- ChromaDB tests require the ChromaDB to be initialized in `/tmp/shogi/chromadb`
