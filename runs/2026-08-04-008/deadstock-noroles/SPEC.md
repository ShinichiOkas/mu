# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## 操作的定義
- **死に筋商品 (Deadstock)**: 一定期間の純売上数（売上数 - 返品数）が極端に低い、または在庫数に対して回転率が著しく低い商品。
- **純売上数**: sales.csvの数量合計からreturns.csvの数量合計を差し引いた値。

## 受入基準
- [ ] CSVファイルの読み込みとデータ集計（検査: `Get-Content inventory.csv, sales.csv, returns.csv` → 出力に「各ファイルのヘッダーおよびデータ行が正常に読み込まれること」を含むこと）
- [ ] 純売上数の計算（検査: `powershell -Command "$s = Import-Csv sales.csv; $r = Import-Csv returns.csv; $s | Group-Object 商品コード | Select-Object Name, @{N='NetSales'; E={ ($_.Group | Measure-Object 数量 -Sum).Sum - (($r | Where-Object 商品コード -eq $_.Name | Measure-Object 数量 -Sum).Sum) }}"` → 出力に「商品ごとの純売上数が算出され、返品が多い商品は低数値または負数になること」を含むこと）
- [ ] 死に筋商品の判定と報告書出力（検査: `powershell -Command "$inv = Import-Csv inventory.csv; $s = Import-Csv sales.csv; $r = Import-Csv returns.csv; $report = foreach($i in $inv){ $sold = ($s | Where-Object 商品コード -eq $i.商品コード | Measure-Object 数量 -Sum).Sum; $ret = ($r | Where-Object 商品コード -eq $i.商品コード | Measure-Object 数量 -Sum).Sum; $net = $sold - $ret; if($net -le 10){ '商品名: ' + $i.商品名 + ' (コード:' + $i.商品コード + ') 原因: 純売上数' + $net + '個と低いため' }}; $report | Out-File report.txt"; Get-Content report.txt` → 出力に「純売上数が閾値（例: 10個以下）の商品が抽出され、理由と共にreport.txtに保存されること」を含むこと）

## 仕様
inventory.csv, sales.csv, returns.csvを解析し、商品ごとの【純売上数 = 合計販売数 - 合計返品数】を算出。純売上数が極めて低い商品を『死に筋商品』と定義し、その根拠（数値）を添えた報告書(report.txt)を作成する。
