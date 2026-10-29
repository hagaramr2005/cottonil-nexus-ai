# Read-only local integration check. Requires running V13-patched FastAPI.
# For auth-enabled development use $env:NEXUS_TEST_BEARER (do not store token in source).
param(
  [string]$ApiBase = 'http://127.0.0.1:8001',
  [string]$FrontendBase = ''
)
$ErrorActionPreference = 'Stop'
$headers = @{}
if ($env:NEXUS_TEST_BEARER) { $headers['Authorization'] = 'Bearer ' + $env:NEXUS_TEST_BEARER }
function Ask([string]$Question, [array]$History = @()) {
  $body = @{ question = $Question; language = 'auto'; page = 'ai'; history = $History } | ConvertTo-Json -Depth 8 -Compress
  return Invoke-RestMethod -Method Post -Uri "$ApiBase/api/copilot/chat" -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
}
Write-Host 'Checking Copilot status...' -ForegroundColor Cyan
$status = Invoke-RestMethod -Uri "$ApiBase/api/copilot/status" -Headers $headers
$status | ConvertTo-Json -Depth 5
Write-Host 'Checking Arabic greeting...' -ForegroundColor Cyan
$greeting = Ask 'مرحبا'
if ($greeting.mode -ne 'conversational' -or $greeting.language -ne 'ar' -or $greeting.answer -notmatch 'أهل') { throw 'Arabic greeting failed.' }
Write-Host "PASS: $($greeting.answer)"
Write-Host 'Checking grounded cases...' -ForegroundColor Cyan
$risks = Ask 'What are the main business risks in Cottonil?'
if (@($risks.cases).Count -lt 1) { throw 'Recorded cases were not returned.' }
Write-Host ('PASS: ' + @($risks.cases).Count + ' cases; mode=' + $risks.mode)
Write-Host 'Checking Arabic follow-up...' -ForegroundColor Cyan
$hist = @(@{ role = 'user'; content = 'What are the main business risks in Cottonil?' },
          @{ role = 'assistant'; content = [string]$risks.answer })
$followup = Ask 'اشرحلي المشكلة التانية بالعربي' $hist
if ($followup.language -ne 'ar' -or @($followup.cases).Count -ne 1 -or $followup.cases[0].id -ne 'NEX-002') { throw 'Arabic follow-up did not resolve NEX-002.' }
Write-Host 'PASS: Follow-up resolved NEX-002'
if ($FrontendBase) {
  Write-Host 'Checking frontend proxy path...' -ForegroundColor Cyan
  $response = Invoke-WebRequest -Uri "$FrontendBase/api/copilot/status" -Headers $headers -UseBasicParsing
  if ($response.StatusCode -ne 200) { throw 'Frontend proxy status check failed.' }
  Write-Host 'PASS: Frontend proxy /api/copilot/status returned 200'
}
Write-Host 'Local read-only Copilot smoke tests passed.' -ForegroundColor Green
