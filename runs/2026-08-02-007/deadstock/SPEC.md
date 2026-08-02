# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## 操作的定義
- **実質販売数**: sales.csvにおける当該商品の数量合計から、returns.csvにおける当該商品の数量合計を差し引いた値。
- **死に筋商品**: 実質販売数が0件である、またはinventory.csvに記載があるがsales.csvに一度も出現しない商品。
- **報告書**: UTF-8形式のテキストファイル（deadstock_report.txt）であり、死に筋商品のリストと、その判定根拠（実質販売数）が明記されていること。

## 受入基準
- [ ] 報告書ファイル deadstock_report.txt が生成されていること。（検査: `Test-Path deadstock_report.txt` → 出力に「True」を含むこと）
- [ ] 報告書内に死に筋商品であることの判定根拠（実質販売数などの数値）が含まれていること。（検査: `Get-Content deadstock_report.txt` → 出力に「実質販売数」を含むこと）

## 仕様
在庫表(inventory.csv)、売上履歴(sales.csv)、返品履歴(returns.csv)を用いて、死に筋商品を特定し、報告書 'deadstock_report.txt' を作成せよ。

【定義】
1. 実質販売数 = (sales.csvの当該商品数量合計) - (returns.csvの当該商品数量合計)
2. 死に筋商品 = 実質販売数が0以下、または売上履歴に一度も登場しない在庫商品

【処理手順】
- inventory.csvにある全商品をベースに、sales.csvとreturns.csvから商品コードをキーにして数量を集計する。
- 上記定義に基づき、死に筋商品を抽出する。
- 出力ファイル 'deadstock_report.txt' には、以下の内容を含めること：
  - 特定された死に筋商品の商品コードと商品名
  - その商品がなぜ死に筋と判定されたかの根拠（具体的に「実質販売数：X個」などの形式で記載）

【成果物】
- deadstock_report.txt (UTF-8)
