$reportContent = @"
ホッチキス
判定根拠：売上合計 0個 - 返品合計 0個 = 実質販売数 0個
蛍光ペン
判定根拠：売上合計 0個 - 返品合計 0個 = 実質販売数 0個
"@
$reportContent | Out-File -FilePath dead_stock_report.txt -Encoding utf8
