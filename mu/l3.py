"""L3 — 大域的 Plan / 複雑タスクの完遂（オーケストレータ）。

L2（単一 checkable タスクの完遂）を"単位"として組み合わせ、複雑なゴールを
最後まで完遂する。L2 で暗黙だった **大域的 Plan が明示・必須**になる層。

PDCA が完全体で現れる:
  P : 複雑ゴールを「ファイルを生む checkable な単位」へ分解      ← HITL 承認
  D : 各単位を L2 が完遂 → 成果物ファイル                       ← 自律
  C : 成果物ファイルを確認 / L2 の失敗を検知                    ← 自律
  A : 再計画（条件/アプローチ/計画の変更）                      ← HITL 承認

**ファイル・グラウンディング**: 各単位が成果物ファイルを生む＝checkable かつ
次の単位への文脈。**判断は外へ、実行は内で** — D・C は自律、P・A は上位
（人間 or L4）に上げる。承認者は呼び出し側が差し込むスロット（`approve`）。
上限は呼び出し側が規定、再帰の底は人間。
"""

from __future__ import annotations

import json
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l2 import Agent, _transcript

# 単位（unit）: task / 出力ファイル / checkable な成功条件。
_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "file": {"type": "string"},
                    "criterion": {"type": "string"},
                },
                "required": ["task", "file", "criterion"],
            },
        }
    },
    "required": ["units"],
}
_ANALYZE_SCHEMA = {
    "type": "object",
    "properties": {"reason": {"type": "string"}, "suggestion": {"type": "string"}},
    "required": ["reason", "suggestion"],
}
_OVERALL_SCHEMA = {
    "type": "object",
    "properties": {"passed": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["passed", "reason"],
}

_PLAN_SYSTEM = (
    "You are a planner. Decompose the GOAL into a short ordered list of small units "
    "(usually 2-3). Each unit MUST produce ONE concrete file deliverable: its 'file' must be "
    "a non-empty, specific path (e.g. calc.py). A unit whose file would be empty is invalid. "
    "The criterion is how that file is checked; for code it is that its tests pass, and the "
    "tests must be an earlier separate unit. "
    "Do NOT create a unit whose only job is to run, execute, verify, or confirm something — "
    "running and verification are already part of each unit's criterion, never a unit of their own. "
    "Order units so that dependencies (via files) come first. "
    "Do NOT add units the goal does not require (no CI, linting, packaging, or restructuring). "
    "Use simple, concrete file paths (e.g. calc.py, not src/calc.py). "
    "Reply as JSON {units:[{task,file,criterion}]} with at least one unit."
)
_REPLAN_SYSTEM = (
    "You are a planner revising a plan after a problem. Given the GOAL, the CURRENT PLAN "
    "(with done-status) and a FAILURE ANALYSIS, produce a revised full plan: change the "
    "conditions, approach, or split/redefine the FAILED unit as needed. "
    "Keep the SAME file paths for units that are already done — never rename or move them. "
    "Each unit's 'file' must be a non-empty, specific path; a unit whose file would be empty is invalid. "
    "Do NOT create a unit whose only job is to run, execute, verify, or confirm something — "
    "running and verification are already part of each unit's criterion, never a unit of their own. "
    "Do NOT add units the goal does not require (no CI, packaging, restructuring). "
    "Reply as JSON {units:[{task,file,criterion}]}."
)
_ANALYZE_SYSTEM = (
    "You diagnose why a sub-task failed. Given the failed UNIT and the TRANSCRIPT of the "
    "attempt, explain briefly why it failed (ill-defined / not checkable, too large, wrong "
    "approach, or a missing dependency) and what to change. Reply as JSON {reason,suggestion}."
)
_OVERALL_SYSTEM = (
    "You are a strict but fair verifier deciding whether an overall GOAL is complete. "
    "You are given the GOAL and the list of DELIVERABLES with their done-status. "
    "A unit marked [x] is DONE: it has already produced its file and passed its own "
    "checkable criterion, verified by execution. Trust this — do NOT ask for file contents "
    "and do NOT try to re-run or re-verify individual files. "
    "Judge ONLY whether the set of DONE deliverables covers everything the GOAL requires "
    "(scope completeness). If every output the goal requires is present and done, answer "
    "passed=true. Answer passed=false only if the goal clearly needs an output that is "
    "missing or not yet done. Reply as JSON {passed,reason}."
)


def _identity_approve(units: list) -> list:
    return units


def _noop(_event: Any) -> None:
    pass


class Orchestrator:
    """L3。大域 Plan を立て、各単位を L2 に完遂させ、失敗は分析して再計画する。"""

    def __init__(self, l0: Any, l2: Any = None) -> None:
        self._l0 = l0
        self._l2 = l2 if l2 is not None else Agent(l0)

    def run(
        self,
        model: str,
        goal: str,
        tools: Sequence[Tool],
        *,
        approve: Callable[[list], list] = _identity_approve,
        log: Callable[[Any], None] = _noop,
        max_rounds: int = 8,
        l2_max: int = 6,
        l2_l1_max: int = 10,
    ) -> dict:
        units = approve(self._plan(model, goal))          # P（HITL 承認）
        log(("plan", units))

        for _ in range(max_rounds):
            pending = [u for u in units if not u.get("done")]
            if pending:
                unit = pending[0]
                msgs, passed = self._l2.run(              # D
                    model, self._unit_goal(unit), tools, max_rounds=l2_max, l1_max=l2_l1_max
                )
                if passed:                                # C: 成功
                    unit["done"] = True
                    log(("unit_done", unit))
                    continue
                analysis = self._analyze(model, unit, msgs)   # C: 失敗分析
                log(("unit_failed", unit, analysis))
                units = approve(self._replan(model, goal, units, analysis))  # A（HITL）
                log(("replan", units))
            else:
                verdict = self._overall(model, goal, units)    # 全体判定
                log(("overall", verdict))
                if verdict.get("passed"):
                    return {"units": units, "done": True}
                analysis = {"reason": verdict.get("reason", ""), "suggestion": ""}
                units = approve(self._replan(model, goal, units, analysis))  # A（HITL）
                log(("replan", units))

        # 上限に達した。全単位が done なら、最終の全体判定を必ず1回行う
        # （max_rounds 直後に overall がスキップされる取りこぼしを防ぐ）。
        if not [u for u in units if not u.get("done")]:
            verdict = self._overall(model, goal, units)
            log(("overall", verdict))
            return {"units": units, "done": bool(verdict.get("passed"))}
        return {"units": units, "done": False}

    # --- 単位ゴールの組み立て（ファイル・グラウンディング） ---
    @staticmethod
    def _unit_goal(unit: dict) -> str:
        return (
            f"{unit['task']}\n"
            f"出力ファイル: {unit['file']}\n"
            f"成功条件（これを満たすこと）: {unit['criterion']}"
        )

    # --- 生命線の LLM 呼び出し（構造化出力） ---
    def _plan(self, model: str, goal: str) -> list:
        data = self._structured(model, _PLAN_SYSTEM, f"GOAL:\n{goal}", _PLAN_SCHEMA)
        return [dict(u, done=False) for u in data.get("units", [])]

    def _replan(self, model: str, goal: str, units: list, analysis: dict) -> list:
        user = (
            f"GOAL:\n{goal}\n\nCURRENT PLAN:\n{_plan_summary(units)}\n\n"
            f"FAILURE ANALYSIS:\n{json.dumps(analysis, ensure_ascii=False)}\n\nProduce a revised plan."
        )
        data = self._structured(model, _REPLAN_SYSTEM, user, _PLAN_SCHEMA)
        new_units = [dict(u, done=False) for u in data.get("units", [])]
        return _carry_done(units, new_units) or units  # 空応答なら現状維持

    def _analyze(self, model: str, unit: dict, msgs: list) -> dict:
        user = f"UNIT:\n{json.dumps(unit, ensure_ascii=False)}\n\nTRANSCRIPT:\n{_transcript(msgs)}"
        return self._structured(model, _ANALYZE_SYSTEM, user, _ANALYZE_SCHEMA)

    def _overall(self, model: str, goal: str, units: list) -> dict:
        user = f"GOAL:\n{goal}\n\nDELIVERABLES:\n{_plan_summary(units)}"
        return self._structured(model, _OVERALL_SYSTEM, user, _OVERALL_SCHEMA)

    def _structured(self, model: str, system: str, user: str, schema: dict) -> dict:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        resp = self._l0.chat(model, messages, format=schema, think=False)
        return _parse_json(resp.message.content)


def _unit_key(unit: dict) -> str:
    return unit.get("file", "")


def _carry_done(old_units: list, new_units: list) -> list:
    done_files = {_unit_key(u) for u in old_units if u.get("done")}
    for u in new_units:
        if _unit_key(u) in done_files:
            u["done"] = True
    return new_units


def _plan_summary(units: list) -> str:
    return "\n".join(
        f"- [{'x' if u.get('done') else ' '}] {u.get('file')}: {u.get('task')} "
        f"(基準: {u.get('criterion')})"
        for u in units
    )


def _parse_json(content: str) -> dict:
    text = content or ""
    start, end = text.find("{"), text.rfind("}")
    for candidate in (text, text[start : end + 1] if 0 <= start < end else ""):
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict):
            return data
    return {}
