# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for continuous integration and continuous deployment.

## Workflows

### CI Pipeline (ci-python-checks.yml)

**Trigger**: Pull requests to main branch (src/tests changes)

**Jobs**:
- **unit-tests**: Runs unit tests
- **lint**: Runs Ruff linting
- **type-check**: Runs mypy type checking

**Steps**:
1. Checkout code
2. Setup dependencies
3. Run unit tests / Ruff / mypy

### Bundle Validate (ci-bundle-validate.yml)

**Trigger**: Pull requests to main branch (bundle changes)

**Jobs**:
- **bundle-validate**: Validates Databricks bundle configuration

**Steps**:
1. Checkout code
2. Setup Databricks CLI
3. Run bundle validate

### Integration Tests (ci-integration.yml)

**Trigger**: Manual (workflow_dispatch)

**Jobs**:
- **integration**: Runs integration tests (data validation only, no pipeline execution)

**Steps**:
1. Checkout code
2. Setup dependencies
3. Setup Databricks CLI
4. Run integration tests (tests/integration)

**Usage**: Run during development to validate data logic against dev environment

### Integration-Exec Tests (ci-integration-exec.yml)

**Trigger**: Manual (workflow_dispatch)

**Jobs**:
- **integration-exec**: Runs integration-exec tests (job/pipeline execution validation)

**Steps**:
1. Checkout code
2. Setup dependencies
3. Setup Databricks CLI
4. Run integration-exec tests (tests/integration-exec)

**Usage**: Run during development to validate job/pipeline execution

### CD Pipeline (cd.yml)

**Trigger**: Tag pushes

**Jobs**:

#### deploy-test
- **Trigger**: Tags matching `v*.*.*-test`
- **Steps**:
  1. Checkout code
  2. Setup dependencies
  3. Setup Databricks CLI
  4. Validate bundle (test)
  5. Deploy to test environment using Databricks Bundle
  6. Run E2E tests (with TEST_CATALOG=shogi_test)

#### integration-check
- **Trigger**: Tags matching `v*.*.*` (not ending with `-test`)
- **Steps**:
  1. Checkout code
  2. Setup dependencies
  3. Setup Databricks CLI
  4. Run integration tests (dev environment validation)
- **Purpose**: Gate before prod deployment to ensure dev environment data is valid

#### deploy-prod
- **Trigger**: Tags matching `v*.*.*` (not ending with `-test`)
- **Needs**: integration-check
- **Steps**:
  1. Checkout code
  2. Setup dependencies
  3. Setup Databricks CLI
  4. Validate bundle (prod)
  5. Deploy to prod environment using Databricks Bundle

## Required Secrets

The following secrets must be configured in GitHub repository settings:

- `DATABRICKS_HOST`: Databricks Workspace URL
- `DATABRICKS_TOKEN`: Databricks Personal Access Token
- `DATABRICKS_CLUSTER_ID`: Databricks Cluster ID (for integration tests)

## Usage

### Trigger CI

Create a pull request to the main branch. CI will automatically run unit tests, linting, and type checking.

### Run Integration Tests (Manual)

1. Go to GitHub Actions tab
2. Select "Integration Tests" workflow
3. Click "Run workflow"
4. Select branch and run

### Run Integration-Exec Tests (Manual)

1. Go to GitHub Actions tab
2. Select "Integration-Exec Tests" workflow
3. Click "Run workflow"
4. Select branch and run

### Deploy to Test

```bash
git tag v0.1.0-test
git push origin v0.1.0-test
```

This will:
- Deploy to test environment
- Run E2E tests

### Deploy to Prod

```bash
git tag v0.1.0
git push origin v0.1.0
```

This will:
- Run integration tests (dev environment validation)
- Deploy to prod environment (only if integration tests pass)

## Deployment Flow

1. **Development**: Run unit tests (CI), integration/integration-exec tests (manual as needed)
2. **Test Deployment**: Create test tag → deploy-test → E2E tests → manual testing
3. **Prod Deployment**: Create prod tag → integration-check → deploy-prod

## Deployment Targets

### Test
- Mode: development
- Workflow name: `shogi-kifu-rag-data-pipeline-test`
- Runs E2E tests after deployment (with TEST_CATALOG=shogi_test)

### Production (prod)
- Mode: production
- Workflow name: `shogi-kifu-rag-data-pipeline-prod`
