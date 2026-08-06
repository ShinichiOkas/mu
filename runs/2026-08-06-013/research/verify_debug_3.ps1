$content = Get-Content comparison_report.md -Raw
Write-Output "Length: $($content.Length)"
Write-Output "Starts with: $($content.Substring(0, 20))"
Write-Output "Contains 結論: $($content -like "*結論*")"
