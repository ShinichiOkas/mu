# File Mapping Document

## Implementation Files and Roles
- **chat_common.py**: chat_common.py — CLI / probe が共有する実況・環境接地の共通部（層の外）。
- **l0_chat.py**: l0_chat.py — L0 を直接触るための最小 CLI チャット。
- **l1_chat.py**: l1_chat.py — L1（ツールコールのループ）を触る最小 CLI チャット。
- **l2_chat.py**: l2_chat.py — L2（PDCA / Reflect ループ）を触る最小 CLI。
- **l3_chat.py**: l3_chat.py — L3（大域 Plan / 複雑タスクの完遂）を触る最小 CLI。
- **l4_chat.py**: l4_chat.py — L4（進行の層 / PjM）を単体で触る最小 CLI。
- **l5_chat.py**: l5_chat.py — L5（目的の層 / PdM）を触る最小 CLI。目的を1行入れると全層が動く。
- **probe_hard.py**: probe_hard.py — 難課題セット（H1〜H6）で L5（目的）＋L4（進行）の構造を負荷テストする probe。
- **probe_learning.py**: probe_learning.py — L6（学習の層）の中核能力＝診断を、機構ゼロで単体測定する probe。
- **probe_standing.py**: probe_standing.py — 継続責務（北極星）を現行の層に渡して L6 の落差を採る probe。
- **tools.py**: tools.py — 検証用の最小ツール群。

Total count of files: 11

| Role | File | Description |
| :--- | :--- | :--- |
| L0 | l0_chat.py | L0 を直接触るための最小 CLI チャット。 |
| L1 | l1_chat.py | L1（ツールコールのループ）を触る最小 CLI チャット。 |
| L2 | l2_chat.py | L2（PDCA / Reflect ループ）を触る最小 CLI。 |
| L3 | l3_chat.py | L3（大域 Plan / 複雑タスクの完遂）を触る最小 CLI。 |
| L4 | l4_chat.py | L4（進行の層 / PjM）を単体で触る最小 CLI。 |
| L5 | l5_chat.py | L5（目的の層 / PdM）を触る最小 CLI。目的を1行入れると全層が動く。 |
| L5 | probe_hard.py | 難課題セット（H1〜H6）で L5（目的）＋L4（進行）の構造を負荷テストする probe。 |
| L0 | chat_common.py | CLI / probe が共有する実況・環境接地の共通部（層の外）。 |
| L0 | tools.py | 検証用の最小ツール群。 |
| L0 | probe_learning.py | L6（学習の層）の中核能力＝診断を、機構ゼロで単体測定する probe。 |
| L0 | probe_standing.py | 継続責務（北極星）を現行の層に渡して L6 の落差を採る probe。 |
