# Review Guidelines

## Objectives

Focus on:

- Correctness
- Maintainability
- Databricks Best Practices
- Performance
- Testing

Do not comment on formatting already handled by Ruff.

---

## Python

- Prefer readable code.
- Use type hints.
- Avoid duplicated logic.
- Minimize nesting.
- Use pathlib instead of os.path.

---

## Spark

Flag:

- collect()
- toPandas()
- unnecessary cache()
- Python loops over DataFrames
- excessive shuffle
- missing partition pruning

Prefer Spark SQL functions over Python UDFs.

---

## Databricks

Verify:

- Unity Catalog compatibility
- Serverless compatibility
- Delta Lake best practices
- Bundle compatibility
- No hard-coded workspace paths

---

## Testing

Check that:

- Unit tests are added.
- Existing tests are updated.
- Edge cases are covered.

---

## Ignore

Do not review:

- generated files
- lock files
- notebooks exported from Databricks

---

## CI

Assume these checks have already passed:

- Ruff
- mypy
- pytest
- Databricks Bundle Validate

Do not repeat those findings.

---

## Pull Request Review

Prioritize:

1. Bugs
2. Data correctness
3. Performance
4. Maintainability
5. Readability
6. コメントは日本語で