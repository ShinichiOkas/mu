$content = Get-Content test_simple.md -Raw
$targets = @("Ollama", "llama.cpp", "vLLM", "LM Studio")
$allTargetsPresent = $true
foreach ($target in $targets) {
    if ($content -notlike "*$target*") {
        $allTargetsPresent = $false
        break
    }
}
$hasHttp = $content -like "*http*"
$hasConclusion = $content -like "*結論*"
if ($allTargetsPresent -and $hasHttp -and $hasConclusion) {
    Write-Output "PASS"
} else {
    Write-Output "FAIL"
}
