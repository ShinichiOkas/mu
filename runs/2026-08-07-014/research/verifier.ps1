$reportPath = "report.md"

if (-not (Test-Path $reportPath)) {
    Write-Output "FAIL: report.md does not exist"
    exit 1
}

$content = Get-Content $reportPath -Raw

# Criteria definitions
$toolNames = @("Tool1", "Tool2", "Tool3", "Tool4")
$viewpoints = @("View1", "View2", "View3", "View4", "View5")
$urlPattern = "http[s]?://\S+"
$keyword = "判断"

$allPassed = $true

# Check tool names
foreach ($tool in $toolNames) {
    if ($content -notmatch [regex]::Escape($tool)) {
        Write-Output "FAIL: Missing tool name $tool"
        $allPassed = $false
    }
}

# Check viewpoints
foreach ($view in $viewpoints) {
    if ($content -notmatch [regex]::Escape($view)) {
        Write-Output "FAIL: Missing viewpoint $view"
        $allPassed = $false
    }
}

# Check for at least one URL
if ($content -notmatch $urlPattern) {
    Write-Output "FAIL: No URL found"
    $allPassed = $false
}

# Check for keyword '判断'
if ($content -notmatch [regex]::Escape($keyword)) {
    Write-Output "FAIL: Keyword '$keyword' not found"
    $allPassed = $false
}

if ($allPassed) {
    Write-Output "PASS"
    exit 0
} else {
    Write-Output "FAIL"
    exit 1
}
