param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$targets = Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -match '^(python|python3|py)\.exe$' -and
    $_.CommandLine -match 'idea_collider_app\.app'
  }

if (-not $targets) {
  Write-Host "No ProMentum app server processes found."
  exit 0
}

foreach ($process in $targets) {
  $label = "$($process.Name) pid=$($process.ProcessId)"
  if ($DryRun) {
    Write-Host "Would stop $label"
    continue
  }
  Stop-Process -Id $process.ProcessId -Force
  Write-Host "Stopped $label"
}
