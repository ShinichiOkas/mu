$content = [System.IO.File]::ReadAllText("comparison_report.md")
Write-Output "Contains 結論: $($content -like "*結論*")"
