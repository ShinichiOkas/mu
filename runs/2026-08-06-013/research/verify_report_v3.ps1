$filePath = "comparison_report.md"
$requiredTerms = @("Ollama", "llama.cpp", "vLLM", "LM Studio", "結論")
$linkPattern = "https?://"

if (-not (Test-Path $filePath)) {
    Write-Host "FAIL: File $filePath not found"
    exit 1
}

$content = Get-Content -Path $filePath -Raw -Encoding UTF8

$allTermsPresent = $true
foreach ($term in $requiredTerms) {
    if ($content -notmatch [regex]::Escape($term)) {
        $allTermsPresent = $false
        Write-Host "FAIL: Missing term: $term"
        break
    }
}

$linkPresent = $content -match $linkPattern
if (-not $linkPresent) {
    Write-Host "FAIL: No HTTP link found"
    $allTermsPresent = $false
}

if ($allTermsPresent -and $linkPresent) {
    Write-Host "PASS"
    exit 0
} else {
    Write-Host "FAIL"
    exit 1
}
