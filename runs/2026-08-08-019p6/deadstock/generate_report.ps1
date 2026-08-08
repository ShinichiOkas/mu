# Deadstock Report Generation Script

# Load inventory
$inventory = Import-Csv "inventory.csv"

# Initialize aggregation hashes
$salesTotals = @{}
$returnsTotals = @{}

# Aggregate sales (Case-insensitive)
Import-Csv "sales.csv" | ForEach-Object {
    $code = $_."商品コード".ToUpper()
    $qty = [int]$_."数量"
    $salesTotals[$code] += $qty
}

# Aggregate returns (Case-insensitive)
Import-Csv "returns.csv" | ForEach-Object {
    $code = $_."商品コード".ToUpper()
    $qty = [int]$_."数量"
    $returnsTotals[$code] += $qty
}

$deadstockItems = @()

# Process each item in inventory
foreach ($item in $inventory) {
    $code = $item."商品コード"
    $name = $item."商品名"
    $upperCode = $code.ToUpper()

    $sales = 0
    if ($salesTotals.ContainsKey($upperCode)) {
        $sales = $salesTotals[$upperCode]
    }

    $returns = 0
    if ($returnsTotals.ContainsKey($upperCode)) {
        $returns = $returnsTotals[$upperCode]
    }

    $netSales = $sales - $returns
    
    # Debugging output as per design.md 2.1
    Write-Host "Item: $code, Sales: $sales, Returns: $returns, NetSales: $netSales"

    if ($netSales -le 0) {
        $deadstockItems += [PSCustomObject]@{
            Code = $code
            Name = $name
            NetSales = $netSales
        }
    }
}

# Generate Report
$report = New-Object System.Collections.Generic.List[string]
$report.Add("死に筋商品一覧")
foreach ($item in $deadstockItems) {
    $report.Add("$($item.Code): $($item.Name)")
}
$report.Add("") # Empty line for spacing
$report.Add("判定理由")
foreach ($item in $deadstockItems) {
    $report.Add("[$($item.Code)] 純売上数量が $($item.NetSales) 個であり、0以下であるため")
}

$report | Out-File -FilePath "deadstock_report.txt" -Encoding utf8

Write-Host "[COMPLETED]"
