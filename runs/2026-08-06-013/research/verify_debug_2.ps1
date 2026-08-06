$reportPath = "comparison_report.md"
$content = Get-Content $reportPath -Raw
Write-Output "Checking targets..."
"Ollama", "llama.cpp", "vLLM", "LM Studio" | ForEach-Object { 
    Write-Output "$_ : $($content -like "*$_*")" 
}
Write-Output "Checking http: $($content -like "*http*")"
Write-Output "Checking 結論: $($content -like "*結論*")"
