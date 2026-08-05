# スプリント009 — l4.py の責務過剰の分析 → PdM を L5 へ分割 実装記録

- 期間: 2026-08-05（分析〜協議〜実装〜受入〜振り返りが1日）
- 合意: [../agreements/009-l4-responsibility-analysis.md](../agreements/009-l4-responsibility-analysis.md)
- 実走記録: [../../runs/2026-08-05-009/README.md](../../runs/2026-08-05-009/README.md)
- ビジョン記録: `~/.claude/pair-agent/vision/009-l4-responsibility-analysis.md`

## 分析（このスプリントの中心）

`l4.py` 777行の責務を13群に実測し、「誰の仕事か」で並べ替えたら**きれいに2列に割れた**。

| | 目的の層（PdM） | 進行の層（PjM） |
|---|---|---|
| 入力 | 人間の**目的** | **SPEC** |
| 判断 | 充足可能か／仕様は何か／verdict と check を見て accept・respec・escalate | プロセスをどう編むか・誰に振るか・どこを再実行するか |
| 生成物 | `SPEC.md` | `PROCESS.md`・成果物・`verdict.md` |
| 概算 | 約185行 | 約320行 |

決め手は行数ではなく **mu 自身の層の定義**（内側を D として使い、外側が判断を足す）。
PdM は PjM を D として使っており、**L2→L3 と同型**だった。
→ 責務過剰の正体は「太った層」ではなく「**2層の同居**」。

## 成果

- **`mu/l4.py` = `Manager`（進行の層／PjM）**: SPEC を受け取り、プロセスを編み、役割を着せた L3 を
  1タスクずつ回し、決定論 check と verdict を集める。**rerun / replan は自分で回し、
  respec / escalate は `outcome` として上へ返す**（PjM の判断語彙は無変更）
- **`mu/l5.py` = `Director`（目的の層／PdM）**: 目的 → 充足可能性の申告 → 仕様 → L4 を D として使い、
  返ってきた verdict / checks で accept / respec / escalate を決める
- **`mu/process.py`**（師匠の判断で追加）: プロセス（タスク列）の状態管理と artifact・判定書の入出力。
  依存グラフは並列可能性の判定と同一物であり、並列実行で触るのもここ
- 予算は各層が自分で持つ（L5_MAX=2 respec サイクル / L4_MAX=3 PjM サイクル）。
  返り値に `l4_rounds` を追加し、**どの層で止まったかが読める**
- CLI: `l5_chat.py`（目的を入力）と `l4_chat.py`（SPEC を入力して進行の層だけ）——層ごとに CLI の規約を回復
- 文書: README の層テーブル・落差の表・役割表・L4/L5 節・facility 一覧・CLI・決定事項、
  各 docstring、roles/pjm.md を同期
- テスト 156 → **166 green**（test_l4=Manager 単体10件・新規／test_l5=目的の層と全体の機構）

### 規模（層の帯にそろった）

```
203 l0 / 189 l1 / 181 l2 / 308 l3 / 318 l4 / 348 l5     ← 層
236 process.py / 153 role_kb.py / 204 tools.py          ← facility
```

## 受入（比較実走）

| 走 | 009 | 008 | |
|---|---|---|---|
| contradiction | escalated・rounds=0・**l4_rounds=0**・1秒 | escalated・0・2秒 | ✅ 同じ |
| bugfix | achieved・1周・76秒 | achieved・1周・487秒 | ✅ 同じ |
| deadstock | achieved（P007・P010）・152秒 | achieved・181秒 | ✅ 同じ |

保護の破れは全走 none。**分割は外から見た振る舞いを変えていない。**

## 学び（Skill 化済み）

- [[suspect-two-layers-before-a-fat-one]]（process・confirmed・新規）
- [[same-vocabulary-different-place-splits-layers]]（process・confirmed・新規）
- [[externalize-only-what-varies-by-use]]（精緻化: facility 抽出＝層を薄くする／層分割＝責務を分ける）

## 振り返り（2026-08-05）

師匠:

> 今回は僕の頭の中に答えがあったけど、あえて言わずにスタートした。結果としてビジョンがぴったり
> 一致したので客観的に見ても正しいビジョンになったのだと思う。

**答えを伏せて独立に分析させ、一致を検証に使った**——006 で言語化した「モデルの非相関」を
ペア自身に適用した形。同じ結論に違う経路（師匠は違和感から、AI は実測と原理の照合から）で
到達したことに意味がある。

## 持ち越し

- **並列実行**（依存グラフは `mu/process.py` に敷設済み。L4 の中の最適化になり L5 は無変更で恩恵を受ける）
- PjM が QA タスクを複数立てると本命の判定書が割れる ／ PMBOK のリスク領域 ／
  証拠デッドロックの記述見直し（`read_file` に offset が無い件）
- L6（L5 の判断スロットに立つ外層）— 「その外に何が来るか」は未着手
