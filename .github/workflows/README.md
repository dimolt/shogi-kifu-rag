# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for continuous integration and continuous deployment.

## Workflows

### CI Pipeline (ci.yml)

**Trigger**: Pull requests to master branch

**Jobs**:
- **test**: Runs unit tests, Ruff linting, and mypy type checking

**Steps**:
1. Checkout code
2. Set up Python 3.12
3. Install uv
4. Install dependencies
5. Run unit tests
6. Run Ruff
7. Run mypy

### CD Pipeline (cd.yml)

**Trigger**: Tag pushes

**Jobs**:

#### deploy-dev
- **Trigger**: Tags matching `v*.*.*-dev`
- **Steps**:
  1. Checkout code
  2. Set up Python 3.12
  3. Install uv
  4. Install dependencies
  5. Deploy to dev environment using Databricks Bundle
  6. Run integration tests

#### deploy-prod
- **Trigger**: Tags matching `v*.*.*` (not ending with `-dev`)
- **Steps**:
  1. Checkout code
  2. Set up Python 3.12
  3. Install uv
  4. Install dependencies
  5. Deploy to prod environment using Databricks Bundle

## Required Secrets

The following secrets must be configured in GitHub repository settings:

- `DATABRICKS_HOST`: Databricks Workspace URL
- `DATABRICKS_TOKEN`: Databricks Personal Access Token
- `DATABRICKS_CLUSTER_ID`: Databricks Cluster ID (for integration tests)

## Usage

### Trigger CI

Create a pull request to the master branch. CI will automatically run.

### Deploy to Dev

```bash
git tag v0.1.0-dev
git push origin v0.1.0-dev
```

### Deploy to Prod

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Deployment Targets

### Development (dev)
- Mode: development
- Workflow name: `shogi-kifu-rag-data-pipeline-dev`
- Runs integration tests after deployment

### Production (prod)
- Mode: production
- Workflow name: `shogi-kifu-rag-data-pipeline-prod`
