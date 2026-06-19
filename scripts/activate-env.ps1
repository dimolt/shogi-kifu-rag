param(
    [ValidateSet("local","remote")]
    [string]$EnvType
)

$venv = ".venv_$EnvType"

& ".\$venv\Scripts\Activate.ps1"