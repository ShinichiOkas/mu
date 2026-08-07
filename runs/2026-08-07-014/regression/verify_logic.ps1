# verify_logic.ps1
# This script verifies that all items listed as 'Dead Stock' in 'dead_stock_report.txt'
# have Actual Sales <= 0 based on source CSVs.

$inventoryFile = "inventory.csv"
$salesFile = "sales.csv"
$returnsFile = "returns.csv"
$reportFile = "dead_stock_report.txt"

if (-not (Test-Path $reportFile)) {
    Write-Host "Report file not found."
    Write-Host "FAIL"
    exit 1
}

# Read CSVs as raw text to avoid encoding/header issues and split manually
function Get-CsvData($path) {
    if (-not (Test-Path $path)) { return @() }
    $lines = Get-Content $path | Where-Object { $_ -match '\S' }
    if ($lines.Count -lt 2) { return @() }
    
    $data = @()
    for ($i = 1; $i -lt $lines.Count; $i++) {
        $data += $lines[$i].Split(',')
    }
    return $data
}

$inventoryData = Get-CsvData $inventoryFile
$nameToCode = @{}
foreach ($row in $inventoryData) {
    if ($row.Count -ge 2) {
        $code = $row[0].Trim()
        $name = $row[1].Trim()
        if ($name) { $nameToCode[$name] = $code }
    }
}

$salesData = Get-CsvData $salesFile
$salesSum = @{}
foreach ($row in $salesData) {
    if ($row.Count -ge 3) {
        $code = $row[1].Trim().ToUpper()
        $qty = 0
        [int]::TryParse($row[2].Trim(), [ref]$qty)
        if ($code) {
            if (-not $salesSum.ContainsKey($code)) { $salesSum[$code] = 0 }
            $salesSum[$code] += $qty
        }
    }
}

$returnsData = Get-CsvData $returnsFile
$returnsSum = @{}
foreach ($row in $returnsData) {
    if ($row.Count -ge 3) {
        $code = $row[1].Trim().ToUpper()
        $qty = 0
        [int]::TryParse($row[2].Trim(), [ref]$qty)
        if ($code) {
            if (-not $returnsSum.ContainsKey($code)) { $returnsSum[$code] = 0 }
            $returnsSum[$code] += $qty
        }
    }
}

# Read Report (UTF8)
$reportLines = Get-Content $reportFile -Encoding utf8
$isValid = $true
$errorMessages = @()

for ($i = 0; $i -lt $reportLines.Count; $i++) {
    $line = $reportLines[$i].Trim()
    if ([string]::IsNullOrWhiteSpace($line)) { continue }

    if ($nameToCode.ContainsKey($line)) {
        $productName = $line
        $productCode = $nameToCode[$productName].ToUpper()
        
        if ($i + 1 -lt $reportLines.Count) {
            $s = 0
            if ($salesSum.ContainsKey($productCode)) { $s = $salesSum[$productCode] }
            
            $r = 0
            if ($returnsSum.ContainsKey($productCode)) { $r = $returnsSum[$productCode] }
            
            $actualSales = $s - $r
            
            if ($actualSales -gt 0) {
                $isValid = $false
                $errorMessages += "Product '$productName' ($productCode) is listed as Dead Stock but has Actual Sales of $actualSales (> 0)."
            }
            $i++ 
        } else {
            $isValid = $false
            $errorMessages += "Product '$productName' is listed but has no corresponding basis line."
        }
    }
}

if ($isValid) {
    Write-Host "PASS"
} else {
    foreach ($msg in $errorMessages) {
        Write-Host $msg
    }
    Write-Host "FAIL"
    exit 1
}
