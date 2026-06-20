# Databricks Asset Bundle

This directory contains the Databricks Asset Bundle configuration for deploying the Shogi Kifu RAG application to Databricks Workspace.

## Structure

- `databricks.yml`: Main bundle configuration
- `resources/notebooks/`: Notebook resource definitions
- `resources/libraries/`: Library resource definitions
- `resources/workflows/`: Workflow resource definitions

## Deployment

### Prerequisites

- Databricks Workspace
- Databricks CLI installed
- Environment variables set:
  - `DATABRICKS_HOST`: Workspace URL
  - `DATABRICKS_TOKEN`: Personal access token

### Deploy to Development

```bash
databricks bundle deploy -t dev
```

### Deploy to Production

```bash
databricks bundle deploy -t prod
```

## Targets

### Development (dev)

- Mode: development
- Workflow name: `shogi-kifu-rag-data-pipeline-dev`

### Production (prod)

- Mode: production
- Workflow name: `shogi-kifu-rag-data-pipeline-prod`

## Resources

### Notebooks

- `step2_silver_table.py`: Silver Table registration
- `step3_gold_table.py`: Gold Table construction
- `step4_floodgate.py`: Floodgate acquisition
- `step5_wikipedia.py`: Wikipedia acquisition
- `step6_chromadb.py`: ChromaDB Vector Store
- `step7_rag_chain.py`: RAG Chain
- `step8_gradio_ui.py`: Gradio UI

### Libraries

- `shared/`: Shared KIF parser modules

### Workflows

- `data_pipeline`: Data pipeline workflow with task dependencies
