$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object Windows.Forms.Form
$form.Text = 'Gemini API - Local setup'
$form.Size = New-Object Drawing.Size(540,230)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $true
$label = New-Object Windows.Forms.Label
$label.Text = 'Paste Gemini API key. Stored encrypted for your Windows account.'
$label.SetBounds(15,15,495,40)
$box = New-Object Windows.Forms.TextBox
$box.UseSystemPasswordChar = $true
$box.SetBounds(15,60,490,28)
$button = New-Object Windows.Forms.Button
$button.Text = 'Save and verify'
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
        $reply = Invoke-RestMethod -Uri 'https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000' -Headers @{'x-goog-api-key'=$key} -TimeoutSec 30
        $models = @($reply.models | Where-Object { $_.supportedGenerationMethods -contains 'generateContent' -and $_.name -match 'flash' -and $_.name -notmatch 'preview|exp|image|audio|tts|live' } | Select-Object -ExpandProperty name)
        if ($models.Count -eq 0) { throw 'No suitable model' }
        $dir = Join-Path $env:LOCALAPPDATA 'TankStorageSecrets'
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        $key | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString | Set-Content -LiteralPath (Join-Path $dir 'gemini.dpapi') -Encoding ASCII
        $model = ($models | Sort-Object -Descending | Select-Object -First 1)
        @{verified_utc=[DateTime]::UtcNow.ToString('o');model=$model;available_models=$models} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'gemini_status.json') -Encoding UTF8
        $box.Clear()
        $key = $null
        $status.Text = 'Saved and connection verified. You may close this window.'
    } catch {
        $status.Text = 'Verification failed. Check key / network and try again.'
    } finally { $button.Enabled = $true }
})
$form.Controls.AddRange(@($label,$box,$button,$status))
$form.AcceptButton = $button
[void]$form.ShowDialog()
