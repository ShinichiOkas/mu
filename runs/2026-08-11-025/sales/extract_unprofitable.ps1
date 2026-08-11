$csvPath = "sales.csv"
$outputPath = "unprofitable_products.txt"

if (-not (Test-Path $csvPath)) {
    Write-Error "Input file $csvPath not found."
    exit 1
}

# Using default encoding since Import-Csv without -Encoding worked in previous test
$data = Import-Csv $csvPath

$unprofitable = New-Object System.Collections.Generic.List[string]

foreach ($row in $data) {
    $revenue = 0.0
    $cost = 0.0
    
    # Use [double]::TryParse to avoid errors with potentially weird formatting
    if ([double]::TryParse($row.販売価格, [ref]$revenue) -and [double]::TryParse($row.原価, [ref]$cost)) {
        if ($revenue -gt 0) {
            $margin = ($revenue - $cost) / $revenue
            if ($margin -lt 0.15) {
                $unprofitable.Add($row.商品)
            }
        }
    }
}

# Output the list to the file
if ($unprofitable.Count -gt 0) {
    $unprofitable | Out-File -FilePath $outputPath -Encoding utf8
} else {
    # Ensure the file is created even if the list is empty
    Out-File -FilePath $outputPath -Encoding utf8
}
