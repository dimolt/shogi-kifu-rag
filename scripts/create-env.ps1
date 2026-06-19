param(
    [ValidateSet("local","remote")]
    [string]$EnvType
)

$venv = ".venv_$EnvType"

Write-Host "Create $venv"

uv venv $venv --python 3.12

& ".\$venv\Scripts\python.exe" -m ensurepip --upgrade