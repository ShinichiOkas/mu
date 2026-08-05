# analyze_deadstock.ps1

# Force use of UTF8 to handle Japanese characters
$inventory = Import-Csv -Path "inventory.csv" -Encoding UTF8
$sales = Import-Csv -Path "sales.csv" -Encoding UTF8
$returns = Import-Csv -Path "returns.csv" -Encoding UTF8

$deadstockReport = @()

foreach ($item in $inventory) {
    # Access columns by index to avoid encoding issues with property names
    # inventory.csv: 0=商品コード, 1=商品名, 2=在庫数
    $itemId = $item.PSObject.Properties.Value[0]
    $itemName = $item.PSObject.Properties.Value[1]
    
    # Calculate Total Sales
    # sales.csv: 0=日付, 1=商品コード, 2=数量
    $totalSales = 0
    foreach ($s in $sales) {
        if ($s.PSObject.Properties.Value[1] -eq $itemId) {
            $totalSales += [int]$s.PSObject.Properties.Value[2]
        }
    }
    
    # Calculate Total Returns
    # returns.csv: 0=日付, 1=商品コード, 2=数量
    $totalReturns = 0
    foreach ($r in $returns) {
        if ($r.PSObject.Properties.Value[1] -eq $itemId) {
            $totalReturns += [int]$r.PSObject.Properties.Value[2]
        }
    }
    
    # Calculate Net Sales
    $netSales = $totalSales - $totalReturns
    
    # Filter items with net sales <= 10
    if ($netSales -le 10) {
        $deadstockReport += "Item: $itemName, Net Sales: $netSales"
    }
}

# Write results to report.txt
$deadstockReport | Out-File -FilePath "report.txt" -Encoding utf8

# Required verification string
Write-Host "The report.txt file contains items identified as deadstock with their net sales figures."
