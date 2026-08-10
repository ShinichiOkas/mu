# Load input files
$inventory = Import-Csv -Path "inventory.csv"
$sales = Import-Csv -Path "sales.csv"
$returns = Import-Csv -Path "returns.csv"

# Aggregate sales and returns by product code (case-insensitive)
$salesCounts = @{}
foreach ($row in $sales) {
    $code = $row."商品コード".ToUpper()
    $qty = [int]$row."数量"
    if (-not $salesCounts.ContainsKey($code)) {
        $salesCounts[$code] = 0
    }
    $salesCounts[$code] += $qty
}

$returnsCounts = @{}
foreach ($row in $returns) {
    $code = $row."商品コード".ToUpper()
    $qty = [int]$row."数量"
    if (-not $returnsCounts.ContainsKey($code)) {
        $returnsCounts[$code] = 0
    }
    $returnsCounts[$code] += $qty
}

# Identify deadstock products
$deadstockList = New-Object System.Collections.Generic.List[PSObject]
foreach ($item in $inventory) {
    $code = $item."商品コード".ToUpper()
    $name = $item."商品名"
    $stock = [int]$item."在庫数"
    
    $totalSales = 0
    if ($salesCounts.ContainsKey($code)) { $totalSales = $salesCounts[$code] }
    
    $totalReturns = 0
    if ($returnsCounts.ContainsKey($code)) { $totalReturns = $returnsCounts[$code] }
    
    $netSales = $totalSales - $totalReturns
    
    # Deadstock Criteria: net sales <= 0
    if ($netSales -le 0) {
        $deadstockList.Add([PSCustomObject]@{
            Code = $item."商品コード"
            Name = $name
            Stock = $stock
            NetSales = $netSales
        })
    }
}

# Generate Report
$reportContent = New-Object System.Collections.Generic.List[string]
$reportContent.Add("死に筋商品一覧")
$reportContent.Add("--------------------------------------------------")

foreach ($item in $deadstockList) {
    $reportContent.Add("$($item.Code) $($item.Name) (在庫数: $($item.Stock)) - 根拠: 純販売数量が$($item.NetSales)個であったため")
}

$reportContent.Add("--------------------------------------------------")
$reportContent.Add("合計死に筋商品数: $($deadstockList.Count)")

$reportContent | Out-File -FilePath "deadstock_report.txt" -Encoding utf8
