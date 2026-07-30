"""L3 — 大域的 Plan / 複雑タスクの完遂（オーケストレータ）。

L2（単一 checkable タスクの完遂）を"単位"として組み合わせ、複雑なゴールを
最後まで完遂する。L2 で暗黙だった **大域的 Plan が明示・必須**になる層。

PDCA が完全体で現れる:
  P : 複雑ゴールを「ファイルを生む checkable な単位」へ分解      ← 承認スロット
  D : 各単位を L2 が完遂 → 成果物ファイル                       ← 自律
  C : 単位の完遂を検知し、完了は**機械的照合**（全単位 done）    ← 自律
  A : 再計画（条件/アプローチ/計画の変更）                      ← 承認スロット

**ファイル・グラウンディング**: 各単位が成果物ファイルを生む＝checkable かつ
次の単位への文脈。**判断は外へ、実行は内で** — 承認者は呼び出し側が差し込む
スロット（`approve`。人間 or L4）。上限は呼び出し側が規定、再帰の底は人間。

L3 の判定は「与えられた仕様（ゴール）を満たしたか」まで。「仕様はそもそも
目的を網羅していたか」は L4 の目的判定が担う。かつてここにあった LLM の
全体判定（overall）は、抽象ゴールに対する推測＝幻覚の温床だった（機序④、
合意005）ため、機械的照合に縮めた。
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l2 import Agent, transcript

# 単位（unit）: task / 出力ファイル / checkable な成功条件。
# check は criterion に埋め込まれた検査コマンド（合意005 決定6）: LLM が定めて明示し、
# 実行と照合はコード側で行う。expect（可視出力）まで見るのが肝 — exit 0 だけでは
# 何も実行しない no-op スクリプトが自明に通る（F1×gemma4 の偽・完遂で実発火）。
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
                    "check": {
                        "type": "object",
                        "properties": {
                            "run": {"type": "string"},
                            "expect": {"type": "string"},
                        },
                    },
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

_PLAN_SYSTEM = (
    "You are a planner. Decompose the GOAL into a short ordered list of small units "
    "(usually 2-3). Each unit MUST produce ONE concrete file deliverable: its 'file' must be "
    "a non-empty, specific path (e.g. calc.py). A unit whose file would be empty is invalid. "
    "File paths must be UNIQUE across units — never plan two units that write the same file; "
    "merge such work into ONE unit instead. "
    "The criterion is how that file is checked; for code it is that its tests pass, and the "
    "tests must be an earlier separate unit. "
    "Do NOT create a unit whose only job is to run, execute, verify, or confirm something — "
    "running and verification are already part of each unit's criterion, never a unit of their own. "
    "Order units so that dependencies (via files) come first. "
    "Do NOT add units the goal does not require (no CI, linting, packaging, or restructuring). "
    "Use simple, concrete file paths (e.g. calc.py, not src/calc.py). "
    "When a unit's criterion can be verified by running a command, ALSO give check: "
    "{run, expect} — run is a PowerShell command exercising the criterion; expect is a "
    "substring that MUST appear in its output (a marker the deliverable is required to "
    "print, e.g. 'SELFTEST OK 12'). Prefer a visible output marker over exit codes alone: "
    "a script that does nothing also exits 0. "
    "Reply as JSON {units:[{task,file,criterion,check?}]} with at least one unit."
)
_REPLAN_SYSTEM = (
    "You are a planner revising a plan after a problem. Given the GOAL, the CURRENT PLAN "
    "(with done-status) and a FAILURE ANALYSIS, produce a revised full plan: change the "
    "conditions, approach, or split/redefine the FAILED unit as needed. "
    "Keep the SAME file paths for units that are already done — never rename or move them. "
    "Each unit's 'file' must be a non-empty, specific path; a unit whose file would be empty is invalid. "
    "File paths must be UNIQUE across units — never two units with the same file; "
    "merge such work into ONE unit instead. "
    "Do NOT create a unit whose only job is to run, execute, verify, or confirm something — "
    "running and verification are already part of each unit's criterion, never a unit of their own. "
    "Do NOT add units the goal does not require (no CI, packaging, restructuring). "
    "When a unit's criterion can be verified by running a command, ALSO give check: "
    "{run, expect} — run is a PowerShell command; expect is a substring that MUST appear "
    "in its output (prefer a visible marker over exit codes alone). "
    "Reply as JSON {units:[{task,file,criterion,check?}]}."
)
_ANALYZE_SYSTEM = (
    "You diagnose why a sub-task failed. Given the failed UNIT and the TRANSCRIPT of the "
    "attempt, explain briefly why it failed (ill-defined / not checkable, too large, wrong "
    "approach, or a missing dependency) and what to change. Reply as JSON {reason,suggestion}."
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
        system: str | None = None,
        max_rounds: int = 8,
        l2_max: int = 6,
        l2_l1_max: int = 10,
    ) -> dict:
        units = approve(self._plan(model, goal))          # P（承認スロット）
        log(("plan", units))

        # rounds は消費した周回数。1 周 = 1 単位実行（失敗周は分析＋再計画を含む）。
        # 上限到達の判別（done=False かつ rounds==max_rounds）のため返り値に含める。
        rounds = 0
        for _ in range(max_rounds):
            pending = [u for u in units if not u.get("done")]
            if not pending:
                break
            rounds += 1
            unit = pending[0]
            msgs, passed = self._l2.run(                  # D
                model, self._unit_goal(unit), tools,
                system=system, max_rounds=l2_max, l1_max=l2_l1_max,
            )
            if passed:                                    # C: 成功（LLM の判定）
                # verify ゲート: criterion 埋め込みの check をコード側で実行・照合する。
                # LLM の pass はここを通って初めて done になる（合意005 決定6）。
                ok, detail = run_check(unit.get("check"), tools)
                if ok is None and unit.get("check"):
                    log(("unit_check_skipped", unit, detail))  # 劣化は黙らせない
                if ok is not False:
                    unit["done"] = True
                    log(("unit_done", unit))
                    continue
                log(("unit_check_failed", unit, detail))
                # check 失敗の分析は決定的（コード側の事実）— LLM の分析は挟まない。
                analysis = {
                    "reason": f"criterion check failed: {detail}",
                    "suggestion": "make the deliverable actually satisfy the check command "
                                  "(including its expected visible output)",
                }
            else:
                analysis = self._analyze(model, unit, msgs)   # C: 失敗分析
            log(("unit_failed", unit, analysis))
            units = approve(self._replan(model, goal, units, analysis))  # A（承認スロット）
            log(("replan", units))

        # C: 完了は機械的照合 — 全単位が done か（空の計画は「全部 done」に化けさせない）。
        # 各単位は実行で検証済み（L2）なので、ここに LLM の推測を挟まない。
        done = bool(units) and not [u for u in units if not u.get("done")]
        reason = "all units done" if done else ("empty plan" if not units else "pending units remain")
        log(("overall", {"passed": done, "reason": f"{reason} (mechanical)"}))
        return {"units": units, "done": done, "rounds": rounds}

    # --- 単位ゴールの組み立て（ファイル・グラウンディング） ---
    @staticmethod
    def _unit_goal(unit: dict) -> str:
        goal = (
            f"{unit['task']}\n"
            f"出力ファイル: {unit['file']}\n"
            f"成功条件（これを満たすこと）: {unit['criterion']}"
        )
        check = unit.get("check") or {}
        if check.get("run"):
            # check は L2 への契約でもある: 成果物はこのコマンドで検証され、
            # expect が指定されていればその文字列を出力に含む必要がある。
            goal += f"\n検証コマンド（コード側で実行される）: {check['run']}"
            if check.get("expect"):
                goal += f"\n検証コマンドの出力に必ず含めるべき文字列: {check['expect']}"
        return goal

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
        user = f"UNIT:\n{json.dumps(unit, ensure_ascii=False)}\n\nTRANSCRIPT:\n{transcript(msgs)}"
        return self._structured(model, _ANALYZE_SYSTEM, user, _ANALYZE_SCHEMA)

    def _structured(self, model: str, system: str, user: str, schema: dict) -> dict:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        resp = self._l0.chat(model, messages, format=schema, think=False)
        return _parse_json(resp.message.content)


def run_check(check: dict | None, tools: Sequence[Tool]) -> tuple[bool | None, str]:
    """criterion 埋め込みの check をコード側で実行・照合する（層間共用の verify ヘルパ）。

    返り値: (True=合格 / False=不合格 / None=実行できない, 詳細)。
    実行は呼び出し側が注入した execute_command ツールを使う — 環境への接地は
    呼び出し側の責務のまま、mu の層は実行器を持たない。
    """
    run = ((check or {}).get("run") or "").strip()
    if not run:
        return None, "no check command"
    execute = next((func for func, _ in tools if func.__name__ == "execute_command"), None)
    if execute is None:
        return None, "no execute_command tool available"
    try:
        result = execute(run)
    except Exception as e:
        return False, f"check raised: {e}"
    content = str(getattr(result, "content", result))
    ok = getattr(result, "ok", None)
    if ok is None:  # 素の str を返す実行器: 従来契約（exit=N 先頭行）から成否を読む
        ok = content.startswith("exit=0")
    expect = ((check or {}).get("expect") or "").strip()
    if not ok:
        return False, f"command failed: {content[:300]}"
    if expect and expect not in content:
        return False, f"expected output '{expect}' not found in: {content[:300]}"
    return True, content[:300]


def _unit_key(unit: dict) -> str:
    return unit.get("file", "")


def _carry_done(old_units: list, new_units: list) -> list:
    # file は単位の同一性そのもの。file がプラン内で重複すると同一性が壊れ、失敗した
    # 単位まで done に化ける（F1-g で偽・完遂として実発火）。重複 file の done は
    # 引き継がない — 安全側に倒す（済み単位の再実行は起きうるが取り返せる。偽 done は
    # overall が「検証済み」と信頼するため取り返せない）。
    old_c = Counter(_unit_key(u) for u in old_units)
    new_c = Counter(_unit_key(u) for u in new_units)
    done_files = {
        _unit_key(u)
        for u in old_units
        if u.get("done") and old_c[_unit_key(u)] == 1 and new_c[_unit_key(u)] <= 1
    }
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
