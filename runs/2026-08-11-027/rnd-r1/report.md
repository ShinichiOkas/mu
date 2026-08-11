# Performance Report: `list.insert(0, x)` vs `collections.deque.appendleft()`

## 仮説
**問い:** 大量の要素を先頭に挿入する場合、`list.insert(0, x)` と `collections.deque.appendleft()` のどちらが効率的か。

**仮説:** 要素数が増えるにつれて、`collections.deque.appendleft()` は `list.insert(0, x)` よりも大幅に短い実行時間を示す。

**支持条件:**
- 要素数 $N \ge 100,000$ において、`deque.appendleft()` の合計時間が `list.insert(0, x)` よりも少なくとも1桁以上速い場合に支持される。

**棄却条件:**
- 実行時間に統計的な有意差がない、あるいは `list.insert(0, x)` の方が速い場合に棄却される。

## 実験設計
- **目的:** Python のリスト先頭への挿入パフォーマンスを比較する。
- **計測指標:** 壁時計時間（秒）。
- **計測手法:** 
    - `time.perf_counter()` を用いて、空のリストおよびデックに対して要素を挿入するループの時間を計測。
    - 挿入件数 $N = 100,000$ とした。
- **環境:** Python 3.x (CPython)

## 結果
`raw_results.txt` より得られた実測値は以下の通りである。

| 手法 | 実行時間 (秒) |
| :--- | :--- |
| `list.insert(0, x)` | 1.688798 |
| `collections.deque.appendleft()` | 0.003176 |

## 評価
計測結果に基づき、以下の通り評価する。

- **数値比較:** 
    - `list.insert(0, x)`: 1.688798 s
    - `collections.deque.appendleft()`: 0.003176 s
    - 比率: `list.insert` は `deque.appendleft` よりも約 531 倍遅い。

- **結論:** 
    - 実行時間は 1.688798 s 対 0.003176 s であり、支持条件である「1桁以上の差」を十分に満たしている。したがって、**仮説は支持された**。

- **考察:** 
    - `list.insert(0, x)` は Python のリスト（動的配列）において、先頭に要素を挿入するたびに既存の全要素を右にシフトさせる必要があるため、計算量は $O(n)$ となり、全体の挿入時間は $O(n^2)$ になる。
    - 一方で `collections.deque` は双方向連結リストに近い構造を持っており、先頭への挿入は $O(1)$ で完了するため、全体の挿入時間は $O(n)$ となる。この計算量の差が、大規模データにおける圧倒的な速度差として現れた。
