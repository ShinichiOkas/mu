$content = [System.IO.File]::ReadAllText("comparison_report.md")
Write-Output "Content: $content"
Write-Output "Ollama: $($content -like "*Ollama*")"
Write-Output "llama.cpp: $($content -like "*llama.cpp*")"
Write-Output "vLLM: $($content -like "*vLLM*")"
Write-Output "LM Studio: $($content -like "*LM Studio*")"
Write-Output "http: $($content -like "*http*")"
Write-Output "結論: $($content -like "*結論*")"
