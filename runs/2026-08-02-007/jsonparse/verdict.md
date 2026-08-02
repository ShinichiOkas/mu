ACHIEVED: yes
REASON: 1) 'import json' および 'from json' は jsonparse.py に存在しない（Select-String で確認）。2) セルフテスト実行で 'JSONPARSE OK 23' を出力し、23件 >= 20件の要件を満たす。3) SPEC.md は PURPOSE の制約（json モジュール不使用、20件以上セルフテスト、エスケープ/数値網羅）を弱めていない。
GAP: 