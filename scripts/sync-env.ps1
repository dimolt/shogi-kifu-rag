param(
    [ValidateSet("local","remote")]
    [string]$EnvType
)

$venv = ".venv_$EnvType"

if ($EnvType -eq "local") {
    $req = "requirements-local.txt"
}
else {
    $req = "requirements-remote.txt"
}

uv pip sync `
    $req `
    --python ".\$venv\Scripts\python.exe"