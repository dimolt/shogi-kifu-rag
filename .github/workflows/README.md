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

#### deploy-test
- **Trigger**: Tags matching `v*.*.*-test`
- **Steps**:
  1. Checkout code
  2. Set up Python 3.12
  3. Install uv
  4. Install dependencies
  5. Setup Databricks CLI
  6. Validate bundle (test)
  7. Deploy to test environment using Databricks Bundle
  8. Run E2E tests (with TEST_CATALOG=shogi_test)

#### deploy-prod
- **Trigger**: Tags matching `v*.*.*` (not ending with `-test`)
- **Steps**:
  1. Checkout code
  2. Set up Python 3.12
  3. Install uv
  4. Install dependencies
  5. Setup Databricks CLI
  6. Validate bundle (prod)
  7. Deploy to prod environment using Databricks Bundle

## Required Secrets

The following secrets must be configured in GitHub repository settings:

- `DATABRICKS_HOST`: Databricks Workspace URL
- `DATABRICKS_TOKEN`: Databricks Personal Access Token
- `DATABRICKS_CLUSTER_ID`: Databricks Cluster ID (for integration tests)

## Usage

### Trigger CI

Create a pull request to the master branch. CI will automatically run.

### Deploy to Test

```bash
git tag v0.1.0-test
git push origin v0.1.0-test
```

### Deploy to Prod

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Deployment Targets

### Test
- Mode: development
- Workflow name: `shogi-kifu-rag-data-pipeline-test`
- Runs E2E tests after deployment (with TEST_CATALOG=shogi_test)

### Production (prod)
- Mode: production
- Workflow name: `shogi-kifu-rag-data-pipeline-prod`
