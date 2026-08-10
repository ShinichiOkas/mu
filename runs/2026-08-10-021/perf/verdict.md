ITEM 1: PASS — gen_data.py を実行すると data.txt が生成されること（Test-Path "data.txt" → True）

ITEM 2: PASS — data.txt に 1,000,000 行の数値が書き出されていること（Get-Content "data.txt".Count → 1000000）

ITEM 3: PASS — analyze.py が上位 10 件を表示すること（出力に「Top 10」が含まれている：99999 のみ表示される 10 行）

ITEM 4: PASS — analyze.py が 10 区間のヒストグラムを表示すること（出力に「Histogram」という見出しを含む、各区間のカウント値が記載されている 10 行）

ITEM 5: PASS — analyze.py が最後に 'ANALYZE OK <経過秒>' の形式で出力すること（実際には「ANALYZE OK 0.36」が表示されたこと確認済み）

ITEM 6: PASS — analyze.py の処理が 3 秒以内に完了すること（実際の実行時間は 0.36 秒、要件の 3 秒以内を満たしている）

GAP: なし