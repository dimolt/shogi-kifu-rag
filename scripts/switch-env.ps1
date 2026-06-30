param(
    [ValidateSet("pyspark","dbx")]
    [string]$EnvType
)

Write-Host "Rebuilding .venv for $EnvType..."

# Remove existing venv
if (Test-Path ".venv") {
    Remove-Item -Recurse -Force ".venv"
}

# Create fresh venv
uv venv --python 3.12

# Sync with appropriate groups
if ($EnvType -eq "pyspark") {
    uv sync --group pyspark --group devTools
}
else {
    uv sync --group dbx --group devTools
}

# Activate
& ".\.venv\Scripts\Activate.ps1"
