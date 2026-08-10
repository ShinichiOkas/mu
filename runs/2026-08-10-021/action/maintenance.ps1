param([string]$Mode = "quick")
# maintenance.ps1 - environment maintenance runner (mock; do not modify).
# quick mode runs steps 1-2 only. full mode runs all 4 steps.
# Leaves its evidence in maintenance_state.json.
$steps = @("temp-clean", "log-rotate")
if ($Mode -eq "full") { $steps += @("index-rebuild", "integrity-check") }
$done = @()
foreach ($s in $steps) {
    Start-Sleep -Milliseconds 100
    $done += $s
}
$state = @{
    last_run = (Get-Date).ToString("s")
    mode     = $Mode
    steps    = $done
} | ConvertTo-Json
Set-Content -Path "maintenance_state.json" -Value $state
if ($Mode -eq "full") {
    Write-Output ("MAINTENANCE COMPLETE " + $done.Count + "/4")
} else {
    Write-Output ("MAINTENANCE PARTIAL " + $done.Count + "/4 (full run requires -Mode full)")
}
