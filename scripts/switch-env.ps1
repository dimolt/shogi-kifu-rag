param(
    [ValidateSet("pyspark","dbx")]
    [string]$EnvType
)

Write-Host "Rebuilding .venv for $EnvType..."

if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    deactivate
}

if (Test-Path ".venv") {
    try {
        Remove-Item -Recurse -Force ".venv" -ErrorAction Stop
    }
    catch {
        throw " .venv の削除に失敗しました。python.exe を使っているプロセスを終了してから再実行してください。"
    }
}

uv venv .venv --python 3.12

if ($EnvType -eq "pyspark") {
    uv sync --group pyspark --group devTools
}
else {
    uv sync --group dbx --group devTools
}