$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object Windows.Forms.Form
$form.Text = 'Claude API - Local setup'
$form.Size = New-Object Drawing.Size(540,230)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $true
$label = New-Object Windows.Forms.Label
$label.Text = 'Paste Claude API key. Stored encrypted for your Windows account.'
$label.SetBounds(15,15,495,40)
$box = New-Object Windows.Forms.TextBox
$box.UseSystemPasswordChar = $true
$box.SetBounds(15,60,490,28)
$button = New-Object Windows.Forms.Button
$button.Text = 'Save and test'
$button.SetBounds(15,100,150,32)
$status = New-Object Windows.Forms.Label
$status.SetBounds(15,140,490,40)
$button.Add_Click({
    $button.Enabled = $false
    $status.Text = 'Checking connection...'
    $form.Refresh()
    try {
        $key = $box.Text.Trim()
        if ($key.Length -lt 20) { throw 'Invalid input' }
        $model = 'claude-haiku-4-5'
        $body = @{model=$model;max_tokens=32;messages=@(@{role='user';content='Reply only CONNECTION_OK'})} | ConvertTo-Json -Depth 8
        $reply = Invoke-RestMethod -Method Post -Uri 'https://api.anthropic.com/v1/messages' -Headers @{'x-api-key'=$key;'anthropic-version'='2023-06-01'} -ContentType 'application/json' -Body $body -TimeoutSec 30
        $answer = ($reply.content | Where-Object type -eq 'text' | ForEach-Object text) -join ''
        if ($answer -notmatch 'CONNECTION_OK') { throw 'Unexpected test response' }
        $models = @($model)
        $dir = Join-Path $env:LOCALAPPDATA 'TankStorageSecrets'
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        $key | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString | Set-Content -LiteralPath (Join-Path $dir 'claude.dpapi') -Encoding ASCII
        $model = ($models | Sort-Object -Descending | Select-Object -First 1)
        @{verified_utc=[DateTime]::UtcNow.ToString('o');model=$model;available_models=$models} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'claude_status.json') -Encoding UTF8
        $box.Clear()
        $key = $null
        $status.Text = 'CONNECTION_OK - Saved. You may close this window.'
    } catch {
        $status.Text = 'Verification failed. Check key / network and try again.'
    } finally { $button.Enabled = $true }
})
$form.Controls.AddRange(@($label,$box,$button,$status))
$form.AcceptButton = $button
[void]$form.ShowDialog()

