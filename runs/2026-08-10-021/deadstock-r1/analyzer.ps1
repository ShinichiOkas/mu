
# Load inventory data
$inventory = Import-Csv "inventory.csv" -Encoding UTF8

# Load sales data
$sales = Import-Csv "sales.csv" -Encoding UTF8

# Load returns data
$returns = Import-Csv "returns.csv" -Encoding UTF8

$deadstock = New-Object System.Collections.Generic.List[PSObject]

foreach ($item in $inventory) {
    $code = $item."商品コード"
    $name = $item."商品名"
    
    # Calculate total sales for this item (case-insensitive)
    $totalSales = 0
    foreach ($sale in $sales) {
        if ($sale."商品コード" -ieq $code) {
            $totalSales += [int]$sale."数量"
        }
    }
    
    # Calculate total returns for this item (case-insensitive)
    $totalReturns = 0
    foreach ($ret in $returns) {
        if ($ret."商品コード" -ieq $code) {
            $totalReturns += [int]$ret."数量"
        }
    }
    
    $netSales = $totalSales - $totalReturns
    
    if ($netSales -le 0) {
        $deadstock.Add([PSCustomObject]@{
            "Item Code" = $code
            "Item Name" = $name
            "Net Sales" = $netSales
        })
    }
}

if ($deadstock.Count -eq 0) {
    "no deadstock" | Out-File "deadstock_report.txt" -Encoding UTF8
} else {
    # Output header and items
    $report = New-Object System.Collections.Generic.List[string]
    $report.Add("Item Code,Item Name,Net Sales")
    foreach ($d in $deadstock) {
        $report.Add("$($d."Item Code"),$($d."Item Name"),$($d."Net Sales")")
    }
    $report | Out-File "deadstock_report.txt" -Encoding UTF8
}
