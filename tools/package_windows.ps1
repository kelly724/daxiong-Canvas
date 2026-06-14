param(
    [string]$PackageName = "Infinite-Canvas-Windows",
    [switch]$IncludeUserData,
    [switch]$NoZip
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir
$versionFile = Join-Path $root "VERSION"
$version = if (Test-Path -LiteralPath $versionFile) {
    (Get-Content -LiteralPath $versionFile -Raw).Trim()
} else {
    "dev"
}

if ([string]::IsNullOrWhiteSpace($version)) {
    $version = "dev"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$distRoot = Join-Path $root "dist"
$packageDir = Join-Path $distRoot "$PackageName-$version-$stamp"
$zipPath = "$packageDir.zip"

if (Test-Path -LiteralPath $packageDir) {
    throw "Package directory already exists: $packageDir"
}
if ((-not $NoZip) -and (Test-Path -LiteralPath $zipPath)) {
    throw "Zip file already exists: $zipPath"
}

New-Item -ItemType Directory -Path $packageDir -Force | Out-Null

$excludedRootDirs = @(
    ".git",
    ".agents",
    ".venv",
    "__pycache__",
    "dist",
    "logs",
    "output"
)

if (-not $IncludeUserData) {
    $excludedRootDirs += "data"
}

$excludedRootFiles = @(
    "history.json",
    "server.err.log",
    "server.out.log",
    "server.run.err.log",
    "server.run.out.log"
)

function Copy-DirectoryContents {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string[]]$ExcludeNames = @()
    )

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        if ($ExcludeNames -contains $_.Name) {
            return
        }
        $target = Join-Path $Destination $_.Name
        Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
    }
}

Get-ChildItem -LiteralPath $root -Force | ForEach-Object {
    if ($_.PSIsContainer) {
        if ($excludedRootDirs -contains $_.Name) {
            return
        }

        if ($_.Name -eq "API") {
            Copy-DirectoryContents -Source $_.FullName -Destination (Join-Path $packageDir "API") -ExcludeNames @(".env")
            return
        }

        if ($_.Name -eq "assets" -and (-not $IncludeUserData)) {
            $assetTarget = Join-Path $packageDir "assets"
            New-Item -ItemType Directory -Path $assetTarget -Force | Out-Null
            foreach ($dir in @("output", "input", "uploads", "library")) {
                $sourceDir = Join-Path $_.FullName $dir
                $targetDir = Join-Path $assetTarget $dir
                if ($dir -eq "output" -and (Test-Path -LiteralPath $sourceDir)) {
                    Copy-Item -LiteralPath $sourceDir -Destination $assetTarget -Recurse -Force
                } else {
                    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                }
            }
            return
        }

        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $packageDir $_.Name) -Recurse -Force
        return
    }

    if ($excludedRootFiles -contains $_.Name) {
        return
    }
    if ($_.Name -like "server.restart.*.log" -or $_.Name -like "server.restart.*.err.log" -or $_.Name -like "server.restart.*.out.log") {
        return
    }
    if ($_.Name -like "*.pyc") {
        return
    }

    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $packageDir $_.Name) -Force
}

foreach ($dir in @(
    "API",
    "data",
    "data\canvases",
    "data\conversations",
    "data\media_previews",
    "assets",
    "assets\input",
    "assets\uploads",
    "assets\library",
    "output",
    "logs"
)) {
    New-Item -ItemType Directory -Path (Join-Path $packageDir $dir) -Force | Out-Null
}

$envExample = @"
# Copy this file to API\.env if you want to preconfigure keys.
# Do not distribute real API keys, tokens, or local Codex paths.
LOVART_BASE_URL=https://lgw.lovart.ai
"@
Set-Content -LiteralPath (Join-Path $packageDir "API\.env.example") -Value $envExample -Encoding UTF8

$readme = @"
# Windows Quick Start

1. Extract the whole folder. Do not move a single bat file out of it.
2. Double-click run.bat.
3. Open http://127.0.0.1:3000/ in the browser.
4. Configure your own API Key, ModelScope, ComfyUI, RunningHub, or Codex CLI in the app settings.

Notes:
- This clean package does not include API\.env, data, logs, root output, or cache files from the packaging machine.
- Codex CLI image generation must be installed, logged in, and synced again on each user's computer.
- If the app reports missing Python dependencies, double-click the dependency installer bat file.
"@
Set-Content -LiteralPath (Join-Path $packageDir "Windows-Quick-Start.md") -Value $readme -Encoding UTF8

if (-not $NoZip) {
    Compress-Archive -LiteralPath $packageDir -DestinationPath $zipPath
    Write-Host "[OK] Package created:"
    Write-Host "     $zipPath"
} else {
    Write-Host "[OK] Package folder created:"
    Write-Host "     $packageDir"
}

Write-Host ""
Write-Host "Clean package excludes API\.env, data, logs, root output, and cache files."
Write-Host "Use -IncludeUserData only if you intentionally want to include local data and generated files."
