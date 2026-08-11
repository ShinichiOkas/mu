$filePath = "story.md"
if (-not (Test-Path $filePath)) {
    Write-Output "FAIL"
    exit 1
}

$content = Get-Content -Path $filePath -Raw
$length = if ($content -eq $null) { 0 } else { $content.Length }

if ($length -ge 800 -and $length -le 1200) {
    Write-Output "PASS"
} else {
    Write-Output "FAIL"
}
