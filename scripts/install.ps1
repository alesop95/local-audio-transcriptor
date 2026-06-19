# Installer pulito per Windows — installa "transcribe" come comando globale isolato (uv tool).
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\install.ps1
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host "Progetto: $ProjectDir" -ForegroundColor Cyan

# 1) Assicura uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installo uv..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

# 2) Installa il tool con gli extra ASR (trascrizione) e GUI
Write-Host "Installo 'transcribe' (puo' richiedere qualche minuto: scarica torch/whisperx)..." -ForegroundColor Yellow
uv tool install --force --python 3.11 "$ProjectDir[asr,gui]"

Write-Host ""
Write-Host "Fatto. Comando disponibile: transcribe" -ForegroundColor Green
Write-Host "Verifica:  transcribe doctor"
Write-Host "GPU NVIDIA? installa torch CUDA: https://pytorch.org/get-started/locally/"
