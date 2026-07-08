param(
    [ValidateSet("pyspark","dbx")]
    [string]$EnvType
)

Write-Host "Rebuilding .venv for $EnvType..."

if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    deactivate
}

uv venv .venv --python 3.12 --clear

if ($EnvType -eq "pyspark") {
    uv sync --group pyspark --group devTools --group web --group rag
}
elseif ($EnvType -eq "dbx") {
    uv sync --group dbx --group devTools --group web --group rag --group ui --group llm
}