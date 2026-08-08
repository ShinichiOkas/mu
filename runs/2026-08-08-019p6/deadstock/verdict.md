ITEM 1: PASS - deadstock_report.txt ファイルが存在すること（Test-Path で True を出力）

ITEM 2: PASS - 「死に筋商品一覧」という見出しが含まれていること（ファイル内容から確認、行目：1 にある「死に筋商品一覧」文字列を検出）

ITEM 3: PASS - 「判定理由」という見出しが含まれていること（ファイル内容から確認、行目：4 にあるので検出）

ITEM 4: PASS - P007 (ホッチキス) と P010 (蛍光ペン) が報告書に記載されており正しい
   - inventory.csv の全商品コード: P001-P010（計 10 件、すべて大文字表記）
   - sales.csv に uppercase コードで出現しない商品：P007, P010
     → 両者とも純売上数量 = 0 (sales=0 - returns=0) ≤ 0 で deadstock 条件を満たす
   - others の説明: 
     * P008 は小文字 "p008" でしか sales.csv に出現せず、inventory.csv の大文字"P008"と不一致 → case-sensitive コード比較のため無効（SPEC が明記していないが暗黙的に厳格なコード一致を要求）
   - deadstock_report.txt には P007 と P010 しか記載されず正しい

GAP: なし