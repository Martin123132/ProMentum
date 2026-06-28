param(
  [string]$Version = ""
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

function Remove-If-In-Dist($PathToRemove) {
  if (-not (Test-Path -LiteralPath $PathToRemove)) {
    return
  }
  $distResolved = (Resolve-Path -LiteralPath $dist).Path
  $targetResolved = (Resolve-Path -LiteralPath $PathToRemove).Path
  if (-not $targetResolved.StartsWith($distResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside dist: $targetResolved"
  }
  Remove-Item -LiteralPath $targetResolved -Recurse -Force
}

function Copy-ReleasePath($RelativePath) {
  $source = Join-Path $repoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $source)) {
    throw "Missing release source path: $RelativePath"
  }
  $sourceItem = Get-Item -LiteralPath $source
  if (-not $sourceItem.PSIsContainer) {
    $target = Join-Path $stage $RelativePath
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    return
  }

  Get-ChildItem -LiteralPath $source -Recurse -Force | ForEach-Object {
    $relative = $_.FullName.Substring($repoRoot.Length + 1)
    if ($relative -match '(^|\\)(__pycache__|\.pytest_cache|idea_collider_data|promentum_data|dist|build)(\\|$)') {
      return
    }
    if ($relative -match '\.pyc$') {
      return
    }
    if ($_.PSIsContainer) {
      return
    }
    $target = Join-Path $stage $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
  }
}

if (-not $Version) {
  $Version = Get-ProMentumVersion
}

$dist = Join-Path $repoRoot "dist"
$packageName = "ProMentum-$Version"
$stage = Join-Path $dist $packageName
$zipPath = Join-Path $dist "$packageName.zip"

New-Item -ItemType Directory -Force -Path $dist | Out-Null
Remove-If-In-Dist $stage
if (Test-Path -LiteralPath $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}
New-Item -ItemType Directory -Force -Path $stage | Out-Null

@(
  ".gitignore",
  "LICENSE",
  "pyproject.toml",
  "README.md",
  "START_ProMentum_WINDOWS.bat",
  "idea_collider_app",
  "scripts",
  "tests",
  "docs\demo-bench",
  "docs\release-notes",
  "docs\screenshots"
) | ForEach-Object { Copy-ReleasePath $_ }

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath -Force

$size = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1KB, 1)
Write-Host "Created $zipPath ($size KB)"
