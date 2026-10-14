# Gera o executável (PyInstaller) e o instalador (Inno Setup) do Gerenciador de Fichas OP.
# Uso, na raiz do projeto:  powershell -ExecutionPolicy Bypass -File build.ps1
# Resultado: dist\GerenciadorFichasOP-<versão>-Setup.exe
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = ".\.venv\Scripts\python.exe"
$iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 não encontrado. Instale em https://jrsoftware.org/isdl.php" }

$versao = & $python -c "from app import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) { throw "Não foi possível ler a versão em app/__init__.py" }
Write-Host "== Gerenciador de Fichas OP $versao ==" -ForegroundColor Cyan

Write-Host "Rodando os testes..."
& $python -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw "Os testes falharam; o build foi cancelado." }

Write-Host "Gerando o executável..."
& $python -m PyInstaller GerenciadorFichasOP.spec --noconfirm --log-level WARN
if ($LASTEXITCODE -ne 0) { throw "O PyInstaller falhou." }

Write-Host "Gerando o instalador..."
& $iscc /Q "/DAppVersion=$versao" instalador\GerenciadorFichasOP.iss
if ($LASTEXITCODE -ne 0) { throw "O Inno Setup falhou." }

Write-Host "Pronto: dist\GerenciadorFichasOP-$versao-Setup.exe" -ForegroundColor Green
