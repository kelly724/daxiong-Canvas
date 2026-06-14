$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir ("codex-cli-sync-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
Start-Transcript -Path $logPath -Force | Out-Null

function Pause-End {
    Write-Host ""
    Write-Host "Log: $logPath"
    Read-Host "Press Enter to close"
    Stop-Transcript | Out-Null
}

function Test-CodexLogin {
    param([string]$CodexPath)
    $loggedIn = $false
    try {
        $output = & $CodexPath login status 2>&1
        $text = ($output | Out-String).ToLowerInvariant()
        if ($LASTEXITCODE -eq 0 -and $text -notmatch "not logged|login required|unauthorized|not authenticated") {
            $loggedIn = $true
        }
    } catch {
        $loggedIn = $false
    }
    if ($loggedIn) { return $true }

    $authPath = Join-Path $HOME ".codex\auth.json"
    if (Test-Path -LiteralPath $authPath) {
        try {
            $raw = Get-Content -LiteralPath $authPath -Raw
            return ($raw -match '"(OPENAI_API_KEY|access_token|refresh_token)"')
        } catch {
            return $false
        }
    }
    return $false
}

function Set-EnvValues {
    param(
        [string]$EnvPath,
        [System.Collections.IDictionary]$Values
    )
    $envDir = Split-Path -Parent $EnvPath
    New-Item -ItemType Directory -Force -Path $envDir | Out-Null
    $lines = @()
    if (Test-Path -LiteralPath $EnvPath) {
        $lines = Get-Content -LiteralPath $EnvPath
    }
    foreach ($key in $Values.Keys) {
        $escaped = [regex]::Escape($key)
        $lines = @($lines | Where-Object { $_ -notmatch "^\s*$escaped\s*=" })
    }
    foreach ($key in $Values.Keys) {
        $lines += "$key=$($Values[$key])"
    }
    [System.IO.File]::WriteAllLines($EnvPath, $lines, [System.Text.UTF8Encoding]::new($false))
}

try {
    Write-Host "=== Codex CLI local auth sync ==="
    Write-Host "Workspace: $root"
    Write-Host ""

    $codex = Get-Command codex -ErrorAction SilentlyContinue
    if (-not $codex) {
        Write-Host "codex command was not found. Install Codex CLI first, then run this script again."
        Pause-End
        exit 1
    }
    $codexPath = $codex.Source
    Write-Host "Codex: $codexPath"
    & $codexPath --version 2>&1 | ForEach-Object { Write-Host $_ }
    Write-Host ""

    & $codexPath exec --help *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "This Codex CLI does not support 'codex exec'. Please upgrade Codex CLI."
        Pause-End
        exit 1
    }

    if (-not (Test-CodexLogin -CodexPath $codexPath)) {
        Write-Host "Codex login state was not detected. Starting 'codex login'..."
        & $codexPath login
        Write-Host ""
    }

    if (-not (Test-CodexLogin -CodexPath $codexPath)) {
        Write-Host "Codex login state is still unavailable. Finish 'codex login' and run this script again."
        Pause-End
        exit 1
    }

    $envPath = Join-Path $root "API\.env"
    $codexAuthDir = Join-Path $HOME ".codex"
    $codexAuthFile = Join-Path $codexAuthDir "auth.json"
    Set-EnvValues -EnvPath $envPath -Values ([ordered]@{
        "CODEX_CLI_USE_LOCAL_AUTH" = "1"
        "CODEX_CLI_AUTH_CONFIGURED" = "1"
        "CODEX_CLI_BIN" = $codexPath
        "CODEX_CLI_AUTH_FILE" = $codexAuthFile
        "CODEX_CLI_HOME" = $codexAuthDir
    })

    Write-Host "Updated API\.env:"
    Write-Host "  CODEX_CLI_USE_LOCAL_AUTH=1"
    Write-Host "  CODEX_CLI_AUTH_CONFIGURED=1"
    Write-Host "  CODEX_CLI_BIN=$codexPath"
    Write-Host "  CODEX_CLI_AUTH_FILE=$codexAuthFile"
    Write-Host "  CODEX_CLI_HOME=$codexAuthDir"
    Write-Host ""
    Write-Host "Testing connectivity..."
    & $codexPath login status 2>&1 | ForEach-Object { Write-Host $_ }
    Write-Host ""
    Write-Host "Done. Refresh API Settings; Codex CLI should show as configured."
    Pause-End
} catch {
    Write-Host "Error: $($_.Exception.Message)"
    Pause-End
    exit 1
}
