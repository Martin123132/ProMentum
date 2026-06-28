param(
  [string]$Version = "",
  [string]$OwnerRepo = "Martin123132/ProMentum",
  [string]$ZipPath = "",
  [string]$WorkRoot = "",
  [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Get-ProMentumVersion {
  $initPath = Join-Path $repoRoot "idea_collider_app\__init__.py"
  $initText = Get-Content -Raw -LiteralPath $initPath
  $match = [regex]::Match($initText, '__version__\s*=\s*"([^"]+)"')
  if (-not $match.Success) {
    throw "Could not read ProMentum version from $initPath"
  }
  return "v$($match.Groups[1].Value)"
}

if (-not $Version) {
  $Version = Get-ProMentumVersion
}

$safeVersion = $Version -replace "[^a-zA-Z0-9._-]", "-"
if ($WorkRoot) {
  New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
  $tempBase = (Resolve-Path -LiteralPath $WorkRoot).Path
} else {
  if (Test-Path -LiteralPath "D:\") {
    New-Item -ItemType Directory -Force -Path "D:\Temp" | Out-Null
    $tempBase = "D:\Temp"
  } else {
    $tempBase = [System.IO.Path]::GetTempPath()
  }
}

$work = Join-Path $tempBase "ProMentumReleaseVerify-$safeVersion-$([System.Guid]::NewGuid().ToString('N'))"
$downloadedZip = Join-Path $work "ProMentum-$Version.zip"
$extractDir = Join-Path $work "unzipped"
$dataDir = Join-Path $work "data"

function Remove-TempWork {
  if (-not (Test-Path -LiteralPath $work)) {
    return
  }
  $baseResolved = (Resolve-Path -LiteralPath $tempBase).Path
  $workResolved = (Resolve-Path -LiteralPath $work).Path
  if (-not $workResolved.StartsWith($baseResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside work root: $workResolved"
  }
  Remove-Item -LiteralPath $workResolved -Recurse -Force
}

try {
  New-Item -ItemType Directory -Force -Path $work, $extractDir, $dataDir | Out-Null

  if ($ZipPath) {
    $sourceZip = (Resolve-Path -LiteralPath $ZipPath).Path
    Copy-Item -LiteralPath $sourceZip -Destination $downloadedZip -Force
    Write-Host "Using local ZIP: $sourceZip"
  } else {
    $url = "https://github.com/$OwnerRepo/releases/download/$Version/ProMentum-$Version.zip"
    Write-Host "Downloading $url"
    Invoke-WebRequest -Uri $url -OutFile $downloadedZip
  }

  Expand-Archive -LiteralPath $downloadedZip -DestinationPath $extractDir -Force

  $required = @(
    "START_ProMentum_WINDOWS.bat",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "idea_collider_app\app.py",
    "idea_collider_app\engine.py",
    "idea_collider_app\storage.py",
    "idea_collider_app\seeds\default_idea_bank.json",
    "idea_collider_app\templates\index.html",
    "idea_collider_app\static\app.js",
    "idea_collider_app\static\app.css",
    "idea_collider_app\static\assets\promentum-workshop.webp",
    "idea_collider_app\static\assets\promentum-console.webp",
    "idea_collider_app\static\assets\spark-bank-workbench.webp",
    "idea_collider_app\static\assets\saved-sparks-shelf.webp",
    "scripts\sample_collisions.py",
    "scripts\stop_dev_processes.ps1",
    "docs\demo-bench\README.md",
    "docs\release-notes\v0.1.3.md",
    "docs\screenshots\promentum-start.png",
    "docs\screenshots\promentum-result.png",
    "docs\screenshots\promentum-share-card.png"
  )
  foreach ($relative in $required) {
    $path = Join-Path $extractDir $relative
    if (-not (Test-Path -LiteralPath $path)) {
      throw "Missing required release file: $relative"
    }
  }

  $allowedScreenshots = @(
    "promentum-start.png",
    "promentum-result.png",
    "promentum-share-card.png"
  )
  $screenshotDir = Join-Path $extractDir "docs\screenshots"
  if (Test-Path -LiteralPath $screenshotDir) {
    $unexpectedScreenshot = Get-ChildItem -LiteralPath $screenshotDir -File -Force |
      Where-Object {
        $_.Name -notin $allowedScreenshots
      } |
      Select-Object -First 1
    if ($unexpectedScreenshot) {
      throw "Release ZIP contains unexpected screenshot file: $($unexpectedScreenshot.FullName)"
    }
  }

  $forbidden = Get-ChildItem -LiteralPath $extractDir -Force -Recurse |
    Where-Object {
      $_.Name -in @(".git", "__pycache__", ".pytest_cache", "idea_collider_data", "promentum_data", "dist", "build") -or
      $_.Extension -eq ".pyc"
    }
  if ($forbidden) {
    throw "Release ZIP contains forbidden generated files: $($forbidden[0].FullName)"
  }

  if (-not $SkipDoctor) {
    Push-Location $extractDir
    try {
      $env:PROMENTUM_HOME = $dataDir
      python -m idea_collider_app.app --doctor | Out-Host
      if ($LASTEXITCODE -ne 0) {
        throw "Doctor command failed."
      }
    } finally {
      Pop-Location
      Remove-Item Env:\PROMENTUM_HOME -ErrorAction SilentlyContinue
    }
  }

  Write-Host "Release ZIP verified for $Version"
} finally {
  Remove-TempWork
}
