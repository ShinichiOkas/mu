# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## 操作的定義
- **死に筋商品**: 在庫表(inventory.csv)に記載がある商品であり、かつ直近3ヶ月間（2026-05-01〜2026-07-31）の正味販売数（sales.csvの数量合計 - returns.csvの数量合計）が0以下である商品。
- **正味販売数**: 特定の商品コードにおける sales.csv の「数量」列の合計値から、returns.csv の「数量」列の合計値を差し引いた数値。

## 受入基準
1. [ ] 報告書ファイル（deadstock_report.txt）が存在すること（検査: `Test-Path deadstock_report.txt` → 出力に「True」を含むこと）
2. [ ] 報告書に「死に筋商品」という見出しが含まれていること（検査: `Get-Content deadstock_report.txt` → 出力に「死に筋商品」を含むこと）
3. [ ] 報告書に判定根拠となる「正味販売数」という用語が含まれていること（検査: `Get-Content deadstock_report.txt` → 出力に「正味販売数」を含むこと）
4. [ ] 在庫表にある全商品（P001, P002, P003, P004）が判定対象として計算に含まれていること（検査: `Get-Content deadstock_report.txt` → 出力に「P004」を含むこと）

## 仕様
在庫表(inventory.csv)、売上履歴(sales.csv)、返品履歴(returns.csv)を用いて、死に筋商品を特定し、報告書『deadstock_report.txt』を作成してください。

【定義】
- 死に筋商品：inventory.csvに存在し、かつ正味販売数が0以下である商品。
- 正味販売数：sales.csvの数量合計からreturns.csvの数量合計を減じた値。

【処理手順】
1. inventory.csv から全商品リストを抽出する。
2. 各商品について、sales.csv と returns.csv から数量を集計し、正味販売数を算出する。
3. 正味販売数が0以下の商品を「死に筋商品」として特定する。
4. 以下の内容を含む報告書(deadstock_report.txt)を作成する：
    - 特定された死に筋商品のリスト（商品コード、商品名）
    - なぜ死に筋と判定したか（算出された正味販売数の値）

【成果物】
- deadstock_report.txt
