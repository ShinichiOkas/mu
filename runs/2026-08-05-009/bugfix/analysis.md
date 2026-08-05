# Bug Analysis Report: buggy_stats.py

## 1. 構造
- **対象ファイル**: `buggy_stats.py`
- **検証基準**: `test_stats.py` および `SPEC.md`
- **分析手法**: 実装コードとテストケースの期待値（Assertion）の比較による不整合の抽出。

## 2. 品質特性と実現構造
- **検証可能性**: 
    - 各関数について、「現在の挙動」と「期待される挙動」を対比させ、具体的にどのテストケースで失敗するかを明記する。
    - 出力形式に `BUG IDENTIFIED` マーカーを付与し、機械的な検知を可能にする。

## 3. 設計規則
- **入力ファイルは読み取り専用**: `SPEC.md`, `test_stats.py` を変更しない。
- **成果物**: `analysis.md` のみを作成する。
- **必須マーカー**: 各バグ項目に `BUG IDENTIFIED` を含める。

---

## 4. バグ分析詳細

### `mean(xs)`
- **現状**: 空リスト `[]` の場合に `0` を返す。
- **期待される挙動**: `test_mean_empty_raises` により、空リストの場合は `ValueError` を送出すること。
- **判定**: **BUG IDENTIFIED**: 空リストに対する例外処理の不足。

### `median(xs)`
- **現状**: 
    1. 空リスト `[]` の場合に `0` を返す。
    2. 要素数が偶数の場合、中央の右側の値をそのまま返す (`s[len(s) // 2]`)。
- **期待される挙動**: 
    1. `test_median_empty_raises` により、空リストの場合は `ValueError` を送出すること。
    2. `test_median_even_is_average_of_middle_two` により、要素数が偶数の場合は中央の2値の平均を返すこと（例: `[1, 2, 3, 4]` -> `2.5`）。
- **判定**: **BUG IDENTIFIED**: 空リストの例外処理不足、および偶数個時の計算ロジック不備。

### `variance(xs)`
- **現状**: 母分散（`n` で割る）を計算している。
- **期待される挙動**: 
    1. `test_variance_is_sample_variance` により、標本分散（`n-1` で割る）を計算すること。
    2. `test_variance_single_raises` により、要素数が1つの場合は `ValueError` を送出すること（`n-1=0` による零除算防止）。
- **判定**: **BUG IDENTIFIED**: 分散の定義が標本分散ではなく母分散になっている。また、単一要素時の例外処理が不足している。

### `value_range(xs)`
- **現状**: `max(xs)` のみを返している。
- **期待される挙動**: 
    1. `test_value_range` により、最大値と最小値の差 (`max - min`) を返すこと（例: `[4, 1, 7]` -> `6`）。
    2. `test_value_range_empty_raises` により、空リストの場合は `ValueError` を送出すること。
- **判定**: **BUG IDENTIFIED**: 範囲（Range）の計算ロジック不備、および空リスト時の例外処理不足。
