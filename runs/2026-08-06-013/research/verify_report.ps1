$filePath = "comparison_report.md"
$requiredTerms = @("Ollama", "llama.cpp", "vLLM", "LM Studio", "conclusion")
$linkPattern = "https?://"

if (-not (Test-Path $filePath)) {
    Write-Host "FAIL"
    exit 1
}

$content = Get-Content -Path $filePath -Raw

$allTermsPresent = $true
foreach ($term in $requiredTerms) {
    if ($content -notmatch [regex]::Escape($term)) {
        $allTermsPresent = $false
        Write-Host "FAIL"
        break
    }
}

$linkPresent = $content -match $linkPattern
if (-not $linkPresent) {
    Write-Host "FAIL"
    $allTermsPresent = $false
}

if ($allTermsPresent -and $linkPresent) {
    Write-Host "PASS"
    exit 0
} else {
    Write-Host "FAIL"
    exit 1
}
