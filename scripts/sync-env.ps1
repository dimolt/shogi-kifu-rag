param(
    [ValidateSet("pyspark","dbx")]
    [string]$EnvType
)

$venv = ".venv_$EnvType"

if ($EnvType -eq "pyspark") {
    $req = "requirements-pyspark.txt"
}
else {
    $req = "requirements-dbx.txt"
}

uv pip sync `
    $req `
    --python ".\$venv\Scripts\python.exe"