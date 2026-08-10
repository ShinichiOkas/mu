# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
jsonparse.py 1ファイルで、標準ライブラリの json モジュールを一切使わずに JSON パーサを実装してくれ。parse(text) が dict/list/str/int/float/bool/None を返す。ネスト・文字列エスケープ（\" \\ \n \uXXXX）・数値（負数・小数・指数）・空配列/空オブジェクト・null/true/false を網羅する20件以上のセルフテストが python jsonparse.py --selftest で走り、全部通れば 'JSONPARSE OK <件数>' を表示して exit 0。

## 操作的定義
- **標準ライブラリの json モジュールを一切使わない**: ソースコード内に 'import json' または 'from json import ...' という記述が一切存在せず、外部のJSON解析ライブラリに依存せずに文字列走査とパースロジックのみで実装されていること。
- **文字列エスケープの網羅**: 以下のエスケープシーケンスを正しくデコードできること：\" (ダブルクォート), \\ (バックスラッシュ), \n (改行), \uXXXX (Unicodeエスケープ)。
- **数値の網羅**: 以下の形式を正しく数値型（int/float）に変換できること：負数（-1）、小数（1.23）、指数表記（1.2e10, -3.4E-5）。
- **セルフテスト**: python jsonparse.py --selftest を実行した際に、内部に保持された20件以上のテストケース（入力文字列と期待される戻り値のペア）をループで検証し、すべての一致を確認する処理。

## 受入基準
1. [ ] jsonparse.py が存在する（検査: `Test-Path jsonparse.py` → 出力に「True」を含むこと）
2. [ ] json モジュールがインポートされていない（検査: `Get-Content jsonparse.py | Select-String 'import json', 'from json'`）
3. [ ] parse(text) 関数が定義されており、dict/list/str/int/float/bool/None を返せる
4. [ ] セルフテストを実行し、20件以上のテストが成功して 'JSONPARSE OK' を表示する（検査: `python jsonparse.py --selftest` → 出力に「JSONPARSE OK」を含むこと）
5. [ ] セルフテスト成功時に exit 0 で終了する（検査: `python jsonparse.py --selftest; if ($? -eq $true) { echo 'EXIT_OK' }` → 出力に「EXIT_OK」を含むこと）

## 仕様
【目的】
標準ライブラリの `json` モジュールを一切使用せず、自前でJSONパーサを実装する。

【実装要件】
1. ファイル名: `jsonparse.py` (単一ファイル)
2. 関数: `parse(text)` を実装し、以下のJSON型をPythonの対応する型に変換して返すこと。
   - Object $\rightarrow$ `dict`
   - Array $\rightarrow$ `list`
   - String $\rightarrow$ `str` (エスケープ `\"`, `\\`, `\n`, `\uXXXX` を正しく処理すること)
   - Number $\rightarrow$ `int` または `float` (負数、小数、指数表記 `e/E` をサポートすること)
   - true/false $\rightarrow$ `True`/`False`
   - null $\rightarrow$ `None`
3. 制約: `import json` および `from json ...` を禁止する。

【テスト要件】
- コマンドライン引数 `--selftest` を指定して実行した際、以下のケースを含む20件以上のテストを自動実行すること。
  - ネストした構造（オブジェクト内の配列、配列内のオブジェクトなど）
  - 文字列エスケープ（`\"`, `\\`, `\n`, `\uXXXX`）
  - 数値（正負の整数、小数、指数表記）
  - 空の配列 `[]` および空のオブジェクト `{}`
  - `null`, `true`, `false` の単体および構造内での出現
- 全テスト通過時、標準出力に `JSONPARSE OK <件数>` (例: `JSONPARSE OK 25`) と出力し、終了コード 0 で終了すること。
