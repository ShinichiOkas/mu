
$inventoryPath = "inventory.csv"
$salesPath = "sales.csv"
$returnsPath = "returns.csv"

$inventoryData = @"
ProductID,ProductName,Category,UnitPrice,StockQuantity
P001,Laptop,Electronics,1000,50
P002,Mouse,Electronics,25,200
P003,Keyboard,Electronics,45,150
P004,Monitor,Electronics,200,80
P005,Desk Chair,Furniture,150,30
P006,Desk Lamp,Furniture,30,100
"@

$salesData = @"
SaleID,ProductID,Quantity,SaleDate
S001,P001,1,2023-01-01
S002,P002,2,2023-01-02
S003,P003,1,2023-01-02
S004,P001,1,2023-01-03
S005,P005,1,2023-01-04
S006,P002,1,2023-01-05
"@

$returnsData = @"
ReturnID,SaleID,ProductID,ReturnDate,Reason
R001,S002,P002,2023-01-06,Defective
R002,S004,P001,2023-01-07,Changed Mind
"@

# Try to remove existing files if they are read-only or held by another process
# In this specific environment, if Set-Content fails due to permission, 
# we try to overwrite using [System.IO.File]::WriteAllText
try {
    [System.IO.File]::WriteAllText((Resolve-Path .).Path + "\" + $inventoryPath, $inventoryData)
    [System.IO.File]::WriteAllText((Resolve-Path .).Path + "\" + $salesPath, $salesData)
    [System.IO.File]::WriteAllText((Resolve-Path .).Path + "\" + $returnsPath, $returnsData)
} catch {
    # Fallback to Set-Content if the .NET method fails
    Set-Content -Path $inventoryPath -Value $inventoryData -Force
    Set-Content -Path $salesPath -Value $salesData -Force
    Set-Content -Path $returnsPath -Value $returnsData -Force
}

Write-Host "Mocks created"
