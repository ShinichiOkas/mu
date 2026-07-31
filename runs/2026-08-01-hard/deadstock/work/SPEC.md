# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## 操作的定義
- **死に筋商品 (Deadstock)**: 直近90日間において、売上数量（sales.csvの数量合計）から返品数量（returns.csvの数量合計）を引いた正味販売数量が0件である商品。
- **報告書 (Report)**: 死に筋商品のリストと、それぞれの正味販売数量（0件であることの証明）を記載したCSVファイル。

## 受入基準
- [ ] 死に筋商品報告書 deadstock_report.csv が生成されていること（検査: `Get-ChildItem deadstock_report.csv` → 出力に「deadstock_report.csv」を含むこと）
- [ ] 報告書に正味販売数量（Net Sales）の列が含まれ、値が0であることを示していること（検査: `Get-Content deadstock_report.csv` → 出力に「Net Sales」を含むこと）

## 仕様
{'purpose': '在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作成する。', 'definitions': {'deadstock': '直近90日間において、売上数量（sales.csv）から返品数量（returns.csv）を差し引いた正味販売数量が0件である商品。', 'report': '死に筋商品の一覧と、その判定根拠（正味販売数量=0）を記載したCSVファイル。'}, 'tasks': ['inventory.csv, sales.csv, returns.csv の3つのファイルを読み込む。', '直近90日間のデータを抽出する。', '商品ごとに [売上数量合計 - 返品数量合計] を計算し、結果が0の商品を特定する。', '特定した商品を deadstock_report.csv というファイルに出力する。列構成は [商品ID, 商品名, 正味販売数量] とすること。'], 'deliverables': ['deadstock_report.csv'], 'verification': [{'text': 'File existence check', 'run': 'Get-ChildItem deadstock_report.csv', 'expect': 'deadstock_report.csv'}, {'text': 'Content verification', 'run': 'Get-Content deadstock_report.csv', 'expect': 'Net Sales'}]}
