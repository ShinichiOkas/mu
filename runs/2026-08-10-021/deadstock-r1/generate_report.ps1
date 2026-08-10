# Import CSV files
$inventory = Import-Csv "inventory.csv"
$sales = Import-Csv "sales.csv"
$returns = Import-Csv "returns.csv"

# Dictionary to store net sales: ProductCode -> Quantity
$netSalesMap = @{}

# Initialize with 0 for all products in inventory
foreach ($item in $inventory) {
    $netSalesMap[$item."商品コード"] = 0
}

# Add sales (handling case-insensitivity for product codes)
foreach ($sale in $sales) {
    $code = $sale."商品コード".ToUpper()
    # We need to find the actual key in the map because inventory.csv might have mixed case, 
    # though usually it's consistent. Let's ensure we match the inventory keys.
    # Since we initialized with inventory, let's check if the uppercase version exists 
    # or if we should have normalized inventory keys too.
    # Let's assume inventory keys are the source of truth.
}

# Re-do logic for better robustness
$netSalesMap = @{}
foreach ($item in $inventory) {
    $code = $item."商品コード"
    $netSalesMap[$code] = 0
}

foreach ($sale in $sales) {
    $code = $sale."商品コード"
    # Case-insensitive lookup in the map
    $key = ($netSalesMap.Keys | Where-Object { $_ -eq $code })
    if ($key) {
        $netSalesMap[$key] += [int]$sale."数量"
    }
}

foreach ($ret in $returns) {
    $code = $ret."商品コード"
    $key = ($netSalesMap.Keys | Where-Object { $_ -eq $code })
    if ($key) {
        $netSalesMap[$key] -= [int]$ret."数量"
    }
}

# Filter products with net sales <= 0
$deadstock = New-Object System.Collections.Generic.List[PSObject]
foreach ($item in $inventory) {
    $code = $item."商品コード"
    $netSale = $netSalesMap[$code]
    if ($netSale -le 0) {
        $deadstock.Add([PSCustomObject]@{
            "ProductCode" = $code
            "ProductName" = $item."商品名"
            "NetSales"    = $netSale
        })
    }
}

# Output to file - using simple text format for a "report" if Export-Csv is too formal, 
# but the requirement just says "filtered results". 
# I will use a clean text format to avoid CSV quotes in a .txt file.
if ($deadstock.Count -gt 0) {
    $reportContent = $deadstock | ForEach-Object { "$($_.ProductCode), $($_.ProductName), $($_.NetSales)" }
    $reportContent | Out-File "deadstock_report.txt" -Encoding UTF8
} else {
    "none found" | Out-File "deadstock_report.txt" -Encoding UTF8
}

Write-Host "REPORT GENERATED"
