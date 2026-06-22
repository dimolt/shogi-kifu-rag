param(
    [ValidateSet("pyspark","dbx")]
    [string]$EnvType
)

$venv = ".venv_$EnvType"

& ".\$venv\Scripts\Activate.ps1"