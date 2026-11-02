param(
    [Parameter(Mandatory=$true)][string]$PromptFile,
    [Parameter(Mandatory=$true)][string]$OutputFile,
    [string]$Model,
    [ValidateRange(128,8192)][int]$MaxOutputTokens = 2048
)
$ErrorActionPreference = 'Stop'
$dir = Join-Path $env:LOCALAPPDATA 'TankStorageSecrets'
$config = Get-Content -LiteralPath (Join-Path $dir 'gemini_status.json') -Raw | ConvertFrom-Json
if (!$Model) { $Model = $config.model }
if ($Model -notin $config.available_models) { throw 'Model was not verified during setup' }
$prompt = Get-Content -LiteralPath $PromptFile -Raw -Encoding UTF8
if ($prompt.Length -gt 60000) { throw 'Prompt exceeds the 60000 character task limit' }
if (Test-Path -LiteralPath $OutputFile) { throw 'Output already exists; reuse it or choose a new output' }
$secret = (Get-Content -LiteralPath (Join-Path $dir 'gemini.dpapi') -Raw).Trim() | ConvertTo-SecureString
$credential = New-Object System.Management.Automation.PSCredential('gemini',$secret)
$body = @{contents=@(@{role='user';parts=@(@{text=$prompt})});generationConfig=@{maxOutputTokens=$MaxOutputTokens}} | ConvertTo-Json -Depth 10
try {
    $response = Invoke-RestMethod -Method Post -Uri "https://generativelanguage.googleapis.com/v1beta/${Model}:generateContent" -Headers @{'x-goog-api-key'=$credential.GetNetworkCredential().Password} -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 180
} catch {
    $safeMessage = 'No diagnostic message'
    $safeMessage = ([string]$_.ErrorDetails.Message) -replace [regex]::Escape($credential.GetNetworkCredential().Password),'[REDACTED]'
    if (!$safeMessage) { $safeMessage = $_.Exception.GetType().Name }
    throw ('Gemini request failed: ' + $safeMessage)
}
$result = @{model=$Model;created_utc=[DateTime]::UtcNow.ToString('o');usage=$response.usageMetadata;candidates=$response.candidates;promptFeedback=$response.promptFeedback}
$result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $OutputFile -Encoding UTF8
Write-Output ('Saved response: ' + $OutputFile)
