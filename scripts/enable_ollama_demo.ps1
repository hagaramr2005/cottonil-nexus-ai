# One-time LOCAL Windows demo setup. No customer data or credentials are sent to Ollama.
# Usage: .\scripts\enable_ollama_demo.ps1 [-Model 'qwen3:4b-instruct']
param(
    [string]$Model = 'qwen3:4b-instruct'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

$ollamaCmd = Get-Command 'ollama' -ErrorAction SilentlyContinue
if ($ollamaCmd) {
    $ollamaExe = $ollamaCmd.Source
} else {
    $ollamaExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (-not (Test-Path $ollamaExe)) {
        throw 'Ollama is not installed. Install the Windows app from https://ollama.com/download, then rerun this script.'
    }
}

function Get-OllamaModels {
    try {
        return Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -Method Get -TimeoutSec 3
    } catch {
        return $null
    }
}

Write-Host 'Checking local Ollama service (127.0.0.1:11434)...'
$tags = Get-OllamaModels
if (-not $tags) {
    Write-Host 'Starting local Ollama server...'
    Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden | Out-Null
    for ($i = 0; $i -lt 20 -and -not $tags; $i++) {
        Start-Sleep -Seconds 1
        $tags = Get-OllamaModels
    }
}
if (-not $tags) {
    throw 'Local Ollama server did not become available. Open Ollama and retry. Do not expose port 11434 publicly.'
}

$installed = @($tags.models | Where-Object { $_.name -eq $Model -or $_.model -eq $Model }).Count -gt 0
if (-not $installed) {
    Write-Host "Downloading model $Model (one-time download; requires internet and disk space)..."
    & $ollamaExe pull $Model
    if ($LASTEXITCODE -ne 0) { throw "ollama pull failed for $Model" }
}

# Verify actual local inference, not only a model tag in the registry.
Write-Host "Testing a short response from $Model..."
$payload = @{ model = $Model; stream = $false; messages = @(@{role='user';content='Respond with the single word READY.'}); options = @{num_predict=32} } | ConvertTo-Json -Depth 8
try {
    $reply = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/chat' -Method Post -Body $payload -ContentType 'application/json; charset=utf-8' -TimeoutSec 120
} catch {
    throw 'Ollama model inference test failed. Check RAM/VRAM and Ollama logs. No application settings were changed.'
}
if (-not $reply.message.content -or -not [string]::IsNullOrWhiteSpace($reply.error)) {
    throw 'Ollama did not return a usable response. No application settings were changed.'
}

$envPath = Join-Path (Get-Location).Path '.env'
if (-not (Test-Path $envPath)) {
    Copy-Item '.env.example' $envPath
    Write-Warning 'Created .env from template. Configure NEXUS_AUTH_SECRET and NEXUS_USERS before starting the app.'
}
$lines = @(Get-Content -Path $envPath -Encoding UTF8)
$settings = [ordered]@{
    NEXUS_LLM_URL = 'http://127.0.0.1:11434/v1/chat/completions'
    NEXUS_LLM_MODEL = $Model
    NEXUS_LLM_TIMEOUT = '60'
    NEXUS_LLM_API_KEY = ''
}
foreach ($key in $settings.Keys) {
    $value = $settings[$key]
    $lines = @($lines | Where-Object { $_ -notmatch ('^\s*' + [regex]::Escape($key) + '\s*=') })
    $lines += "$key=$value"
}
[System.IO.File]::WriteAllLines($envPath, [string[]]$lines, ([System.Text.UTF8Encoding]::new($false)))
Write-Host "Ollama local inference PASSED and .env configured for $Model" -ForegroundColor Green
Write-Host 'Next: .\scripts\start_windows.ps1'
Write-Host 'Check: http://127.0.0.1:8000/api/copilot/status (requires login when auth is enabled)'
Write-Host 'IMPORTANT: Ollama will be used only for supported questions with actual ingested evidence.'
