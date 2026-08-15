---
name: skill が要求した成果物は、プロセスが出力として宣言しないと発行されない
description: skill は「やり方」を渡せるが、成果物の契約はプロセス（PjM のタスク出力）側にある。宣言されない成果物は tray に留まり、共有空間にも次の周にも出ない
type: project
maturity: forming
proposed_by: ai
confirmed_by: 師匠
created_at: 2026-08-15
provenance: mu 044。変異検査 skill が要求した verify_check.md が tray 止まりになった
---

skill に「記録を `verify_check.md` に残せ」と書いても、**その成果物は共有空間に出ない**。
発行（publish-out）されるのは、PjM がタスクの `file` として宣言した出力**だけ**である
（合意030 の single-writer 発行ゲート）。

## Why

mu 044。`verify-the-verifier-by-mutation`（implementer 宛て）は
「検算の記録を verify_check.md に残せ」と要求している。実走で mu はそのとおりに書いた:

```
[tool] write_file(...\.mu-work\implementer\task-3\verify_check.md, ...) -> wrote 2748 bytes
```

**だが tray の中で終わった。** プロセスの当該タスクの宣言出力は README.md であり、
verify_check.md は宣言されていない。よって発行ゲートを通らず、共有空間にも、
次の周（持ち越し）にも、人間の目にも届かない。**検算した証跡が残らない。**

## How to apply

- skill で成果物を要求するときは、**プロセス側にもその出力が立つか**を確かめる。
  立たないなら、要求は「やった形跡が消える指示」になる
- 選択肢は3つ: (a) 定義書（`pjm.md`）に「検算の記録もタスク出力として宣言する」を書く
  (b) skill 側で「その記録を、成果物と同じタスクの宣言出力に含めるよう PjM に求めよ」と書く
  (c) 発行の契約を変える（構造）——scratch と成果物の間に「証跡」の区分を作る
- **やり方（skill）と成果物の契約（プロセス）は別の層にある**。skill だけでは閉じない
- 関連: [[verify-the-verifier-by-mutation]]（この skill が要求している側）
