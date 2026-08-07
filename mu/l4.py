"""L4 — 進行の層（PjM / Manager）。

「どう進めるか」を定義し管理する層。SPEC（何を作るか）を受け取り、**役割注釈付きプロセス**を編み、
役割を着せた L3 に1タスクずつ完遂させ、決定論の検査と独立 QA の判定を集めて、
**自分の職掌で直せる失敗（rerun / replan）は自分で回す**。仕様が悪い・人手が要ると判断したら
（respec / escalate）**上の層へ返す**——判断は外へ、実行は内で（合意009）。

マルチエージェントは新しいフレームワークではなく「役割を着せた L3 の逐次ループ」であり、
並列化は後から足せる最適化にすぎない（合意006）。

  P: SPEC → プロセス（役割注釈付きタスク列。人選も含む）= PROCESS.md            ← PjM（LLM）
  D: 1タスクずつ、役割定義を前置し**役割の権限で絞ったツール**で L3 に完遂させる ← 内側の層
  C: 受入基準の決定論 check ＋ 末尾の QA タスクが書く verdict.md の機械読み      ← コード
  A: rerun / replan は自分で回す。respec / escalate は上へ返す                   ← PjM（LLM）

決定論の床（この層）:
  - プロセス末尾に QA タスクが無ければ**コードが必ず足す**（検証を飛ばして完遂に到達できない）
  - 判定書の契約（ACHIEVED / REASON / GAP）はコードが供給し、成功条件にも入れる
  - 部分再実行の依存伝播はコードが行い、**QA タスクは必ず再実行**（done を carry しない）
  - 受入基準の check（実行＋可視マーカー照合）は verdict とは独立に走る
  - 役割の権限（役割定義の宣言）はコードが適用する。QA は自分の判定書しか書けない
  - 壊れた verdict / 壊れた PjM 判断は安全側（uncertain / escalate）に落ちる

やり方（PjM のプロンプト）は roles/pjm.md にあり、コードには無い。返すべき形はスキーマが
唯一の出所（合意008）。**無状態** — 上限・役割 KB・モデルプールは呼び出し側が規定する。
"""

from __future__ import annotations

import json
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l3 import Orchestrator, _parse_json, _with_env, run_check  # 層間共用ヘルパ
from .process import (
    carry_done_tasks, clear_failure, invalidate, normalize_tasks, read_verdict, summarize,
    task_goal, write_process, process_note,
)
from .role_kb import role_prompt, role_tools, task_roles

# --- スキーマ（ポジションの契約。コードの分岐が依存する） ----------------------

_PROCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "task": {"type": "string"},
                    "file": {"type": "string"},
                    "criterion": {"type": "string"},
                    "check": {
                        "type": "object",
                        "properties": {"run": {"type": "string"}, "expect": {"type": "string"}},
                    },
                    "model": {"type": "string"},
                },
                "required": ["role", "task", "file", "criterion"],
            },
        }
    },
    "required": ["tasks"],
}

_DECIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["rerun", "replan", "respec", "escalate"]},
        "invalidate": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
    "required": ["action", "invalidate", "reason"],
}


def _noop(_event: Any) -> None:
    pass


def _outcome(outcome, reason, tasks, verdict, checks, ok, rounds, process_path) -> dict:
    """上の層への申告。`outcome` は done / respec / escalate。"""
    return {
        "outcome": outcome, "reason": reason, "tasks": tasks, "verdict": verdict,
        "checks": checks, "ok": ok, "rounds": rounds, "process_path": process_path,
    }


# --- 層をまたいで使う生命線のヘルパ（L5 も同じ形で LLM に判断させる） ----------

def lifeline_system(
    roles: dict, role: str, section: str, schema: dict, env: str | None, log: Callable,
) -> str:
    """役割定義（やり方）＋スキーマ由来の契約（形）＋呼び出し側の環境 で system を組む。

    定義書が無ければ「役割は認識しているが知識が無い」状態になる——既定プロンプトで
    埋めず、その事実をログに出す（合意008）。
    """
    doc = role_prompt(roles.get(role, ""), section).strip()
    if not doc:
        log(("role_doc_missing", role, section))
    return _with_env("\n\n".join(s for s in (doc, _shape_line(schema)) if s), env)


def structured(l0: Any, model: str, system: str, user: str, schema: dict) -> dict:
    """構造化出力の1呼び出し（生命線）。層はこの形でしか LLM に判断させない。"""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    resp = l0.chat(model, messages, format=schema, think=False)
    return _parse_json(resp.message.content)


class Manager:
    """L4。SPEC からプロセスを編み、役割を着せた L3 に1タスクずつ完遂させ、検証結果を集める。"""

    def __init__(self, l0: Any, l3: Any = None) -> None:
        self._l0 = l0
        self._l3 = l3 if l3 is not None else Orchestrator(l0)

    def run(
        self,
        model: str,
        spec: dict,
        tools: Sequence[Tool],
        *,
        roles: dict | None = None,
        models: Sequence[str] | None = None,
        purpose: str = "",
        spec_path: str = "SPEC.md",
        process_path: str = "PROCESS.md",
        log: Callable[[Any], None] = _noop,
        system: str | None = None,
        guard: Callable[[], list] | None = None,
        max_rounds: int = 3,
        l3_max: int = 8,
        l2_max: int = 6,
        l2_l1_max: int = 10,
    ) -> dict:
        """SPEC を完遂まで進める。返り値の `outcome` が上の層への申告:

            done     — 受入基準・verdict とも通った
            respec   — 仕様が悪いと PjM が判断した（この層では直せない）
            escalate — 人手が要る／予算が尽きた
        """
        roles = roles or {}
        pool = list(models) if models else [model]
        limits = {"max_rounds": l3_max, "l2_max": l2_max, "l2_l1_max": l2_l1_max}

        tasks = self._process(model, spec, roles, pool, log, system)    # P（体制＝プロセス）
        rounds = 0
        for _ in range(max_rounds):
            rounds += 1
            # 守られるべき入力（原本）が壊れていないかを**周の頭で**見る。壊れた後の作業は
            # すべて偽の前提の上に乗るため、進める意味がない（合意016 ②。015 で実発火）。
            # 保護機構そのものは持たない——呼び出し側が注入する（環境接地は caller の責務）。
            broken = guard() if guard else []
            if broken:
                detail = ", ".join(f"{b.get('path')}({b.get('status')})" for b in broken)
                log(("protection_broken", broken))
                return _outcome(
                    "escalate", f"保護された入力が壊れている: {detail}。"
                    "壊れた入力の上で作業を続けても結果は意味を持たない。人間の確認が要る。",
                    tasks, None, [], False, rounds, process_path,
                )
            write_process(process_path, purpose, tasks, process_note(roles))
            log(("process", tasks, process_path))

            failure = self._execute(model, tasks, tools, roles, pool,   # D（役割を着た L3 の逐次ループ）
                                    spec_path, purpose, system, log, limits)
            checks = _run_criteria_checks(spec, tools)                  # C（決定論の床）
            if checks:
                log(("checks", checks))
            verdict = read_verdict(tasks) if failure is None else None  # C（QA の判定を機械読み）
            if verdict:
                log(("verdict", verdict))
            failed_checks = [c for c in checks if c["ok"] is False]
            ok = failure is None and not failed_checks and bool(verdict) and verdict["achieved"] == "yes"
            if ok:
                return _outcome("done", "", tasks, verdict, checks, True, rounds, process_path)

            decision = self._decide(                                    # A（部分再実行の判断）
                model, spec, tasks, failure, failed_checks, verdict, roles, log, system
            )
            act, reason = decision.get("action"), str(decision.get("reason", ""))
            if rounds < max_rounds:
                if act == "rerun":
                    # 無効化と同時に「なぜ落ちたか」をタスクへ載せる。理由を添えずに再実行させると、
                    # 実行者は成果物でなく検査器の方を直しにいく（013 実走・合意014 A）。
                    # 載せるのはコードが実行した事実だけ——PjM の解釈は混ぜない（合意014 ①）。
                    invalidate(tasks, decision.get("invalidate", []), failure=_failure_facts(failed_checks))
                    continue
                if act == "replan":
                    new = self._process(model, spec, roles, pool, log, system)
                    tasks = carry_done_tasks(tasks, new)
                    continue
            elif act in ("rerun", "replan"):     # 直せるはずだが予算が尽きた → 人手へ
                return _outcome("escalate", f"PjM の予算切れ（{act}）: {reason}",
                                tasks, verdict, checks, False, rounds, process_path)
            # respec / escalate / 壊れた判断 → 自分の職掌では直せない。上の層へ返す。
            up = "respec" if act == "respec" else "escalate"
            return _outcome(up, reason, tasks, verdict, checks, False, rounds, process_path)

        return _outcome("escalate", "rounds exhausted", tasks, None, [], False, rounds, process_path)

    def _execute(
        self, model: str, tasks: list, tools: Sequence[Tool], roles: dict,
        pool: list, spec_path: str, purpose: str, system: str | None,
        log: Callable, limits: dict,
    ) -> dict | None:
        """pending タスクを順に実行する。最初に失敗したタスクを返す（全部成功なら None）。"""
        for i, t in enumerate(tasks):
            if t.get("done"):
                continue
            doc = roles.get(t["role"], "")
            task_system = "\n\n".join(s for s in (role_prompt(doc), system) if s)
            task_model = t.get("model") if t.get("model") in pool else model
            prior = [p["file"] for p in tasks[:i] if p.get("done")]
            task_tools = role_tools(tools, doc, t["file"], t["role"], log)  # 役割別の権限（B1）
            result = self._l3.run(
                task_model, task_goal(t, spec_path, prior, purpose), task_tools,
                log=log, system=task_system or None,
                max_rounds=limits["max_rounds"], l2_max=limits["l2_max"],
                l2_l1_max=limits["l2_l1_max"],
            )
            t["done"] = bool(result.get("done"))
            if t["done"]:
                clear_failure(t)   # 通ったら前回の失敗は捨てる（持つのは直近1回だけ）
            log(("task_done", t) if t["done"] else ("task_failed", t))
            if not t["done"]:
                return t
        return None

    # --- 生命線の LLM 呼び出し（構造化出力） ---
    #
    # やり方（プロンプト）は roles/*.md から来る。コアが供給するのはポジションの契約
    # （スキーマ由来の形の1行）と呼び出し側の環境だけ（合意008）。

    def _process(
        self, model: str, spec: dict, roles: dict, pool: list, log: Callable,
        system: str | None = None,
    ) -> list:
        roles_s = "\n".join(
            f"- {name}: {_first_line(role_prompt(doc))}" for name, doc in roles.items()
        ) or "(none)"
        user = (
            f"SPEC:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
            f"ROLES (your knowledge base):\n{roles_s}\n\n"
            f"AVAILABLE MODELS (default first):\n{', '.join(pool)}"
        )
        data = structured(self._l0, 
            model, lifeline_system(roles, "pjm", "process", _PROCESS_SCHEMA, system, log),
            user, _PROCESS_SCHEMA,
        )
        return normalize_tasks(data.get("tasks", []), task_roles(roles), log)

    def _decide(
        self, model: str, spec: dict, tasks: list, failure: dict | None,
        failed_checks: list, verdict: dict | None, roles: dict, log: Callable,
        system: str | None = None,
    ) -> dict:
        result_parts = []
        if failure is not None:
            result_parts.append(f"FAILED TASK: {json.dumps(failure, ensure_ascii=False)}")
        if failed_checks:
            result_parts.append(
                "FAILED CHECKS:\n" + "\n".join(f"- {c['text']}: {c['detail']}" for c in failed_checks)
            )
        if verdict is not None:
            result_parts.append(f"QA VERDICT: {json.dumps(verdict, ensure_ascii=False)}")
        user = (
            f"SPEC:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
            f"PROCESS:\n{summarize(tasks)}\n\n"
            f"ROUND RESULT:\n" + ("\n".join(result_parts) or "(no info)")
        )
        data = structured(self._l0, 
            model, lifeline_system(roles, "pjm", "decide", _DECIDE_SCHEMA, system, log),
            user, _DECIDE_SCHEMA,
        )
        if data.get("action") not in ("rerun", "replan", "respec", "escalate"):
            data = {"action": "escalate", "invalidate": [], "reason": "unparseable PjM decision"}
        log(("pjm", data))
        return data

def _shape_line(schema: dict) -> str:
    """スキーマから「返すべき JSON の形」の1行を作る（合意008）。

    形は**ポジションの契約**でありコアの持ち物。役割定義書に二重に書かせない
    （書かせるとスキーマとプロンプトが別々に腐る）。スキーマを唯一の出所にする。
    """
    def render(spec: dict) -> str:
        kind = spec.get("type", "string")
        if spec.get("enum"):
            return "|".join(map(str, spec["enum"]))
        if kind == "array":
            return f"[{render(spec.get('items', {}))}]"
        if kind == "object":
            inner = ", ".join(f"{k}: {render(v)}" for k, v in spec.get("properties", {}).items())
            return "{" + inner + "}"
        return kind

    required = set(schema.get("required", []))
    body = ", ".join(
        f"{name}{'' if name in required else '?'}: {render(spec)}"
        for name, spec in schema.get("properties", {}).items()
    )
    return "Reply as JSON: {" + body + "}  ('?' = optional)."


# QA タスクのミニマム定義（検証を飛ばして完遂に到達させないための床）。
# 文面・出力ファイル・成功条件は roles/qa.md の frontmatter で上書きできるが、
# **「QA タスクが存在すること」自体は上書きできない**（合意008。データ側から検証を消せると
# 偽・完遂の経路が再び開く）。
# 判定書の書式＝**コードが正規表現で読む契約**（`read_verdict` と対になる）。
# ポジション側の持ち物なのでコードが供給する。役割定義書に二重に書かせない（合意008）。
# artifact の注記のミニマム（定義書の `## spec-artifact` / `## process-artifact` で上書き可能）。


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip().lstrip("# ")
    return ""


def _failure_facts(failed_checks: list) -> str:
    """落ちた検査を「コードが実行した事実」だけの文面にする（解釈を混ぜない。合意014 ①）。"""
    lines = []
    for c in failed_checks:
        lines.append(f"  検査: {c['run']}")
        lines.append(f"  実際: {c['detail']}")
    return "\n".join(lines)


def _run_criteria_checks(spec: dict, tools: Sequence[Tool]) -> list:
    """criteria を検査の状態つきで返す（決定論の床。verdict とは独立）。

    `kind` は「誰が見たか」の区別（合意015 B）:
      machine    — run を実行して照合した（実体に接地した床）
      unverified — **run が無い＝誰も機械的に見ていない**

    従来は run の無い基準を黙って捨てていたため、外から「検査されたのか、検査項目が
    無かったのか」が区別できなかった——010 で潰した「見えない部分が残る」と同じ形。
    `ok` は None のままなので**完遂判定は変わらない**（床は動かさない）。
    接地できない性質の検査は judge（LLM 検査器）と QA が担う。
    """
    results = []
    for c in spec.get("criteria", []):
        if not c.get("run"):
            results.append({
                "text": c["text"], "run": "", "ok": None, "kind": "unverified",
                "detail": "機械的な検査コマンドが無い（judge / QA の判断に委ねられている）",
            })
            continue
        ok, detail = run_check({"run": c["run"], "expect": c.get("expect", "")}, tools)
        results.append(
            {"text": c["text"], "run": c["run"], "ok": ok, "detail": detail, "kind": "machine"}
        )
    return results


