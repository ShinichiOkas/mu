"""L4 — 目的の層（なぜ作るか / Director）。

L3（詳細な仕様とゴールを与えられ完遂する層）の上に「目的を仕様に変換し、
成果を目的に照らす」層を重ねる。人間が自然に言えるのは目的であり、詳細な
仕様ではない — その落差を埋めるのがこの層（合意005）。

PDCA は L3 と同じ形（再帰同一構造）:
  P : 目的 → 操作的定義 + 完了条件 + 仕様。**定義は artifact（ファイル）**
      に明示する — 推測をなくすのではなく、検証可能な仮定に変える   ← 自律
  D : L3 に仕様を渡して完遂させる（L3 の Plan 承認は L4 が自律）     ← 自律
  C : 成果（ディスク上の実体）を**目的**に照らして判定               ← 自律
  A : 具体的な欠落は自律で仕様を改訂。判定できないときは判定できないと
      分かって**人間に上げる**（review スロット）                    ← HITL

手続きの成功と目的の達成は別の事実である（スクリプトが exit 0 で「該当なし」と
出力しても、本当に該当が無いのか結合キーを間違えたのかは目的を持つ層にしか
区別できない）。だから C は L3 の done を信用せず、成果物ファイルをディスク
から読み直して判定する。判定は yes / no / uncertain の3値で、uncertain を
楽観の yes に倒さないことが偽・完遂の再発防止線。

**無状態**。上限・承認者・レビュー担当は呼び出し側が規定する。再帰の底は人間。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l3 import Orchestrator, _parse_json, _with_env, run_check  # 層間共用ヘルパ

# criteria の各項目は {text, run, expect}: text は条件の記述、run/expect は
# criterion に埋め込まれた検査コマンド（合意005 決定6）。検査は LLM が定めて
# artifact に明示され（人間が直せる）、実行と照合はコード側の事実になる。
_SPECIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "definitions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"term": {"type": "string"}, "definition": {"type": "string"}},
                "required": ["term", "definition"],
            },
        },
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "run": {"type": "string"},
                    "expect": {"type": "string"},
                },
                "required": ["text"],
            },
        },
        "spec": {"type": "string"},
    },
    "required": ["definitions", "criteria", "spec"],
}
_ASSESS_SCHEMA = {
    "type": "object",
    "properties": {
        "achieved": {"type": "string", "enum": ["yes", "no", "uncertain"]},
        "reason": {"type": "string"},
        "gap": {"type": "string"},
    },
    "required": ["achieved", "reason", "gap"],
}

_SPECIFY_SYSTEM = (
    "You turn an abstract PURPOSE (why) into a concrete, checkable specification (what). "
    "1) definitions: define every vague or domain term OPERATIONALLY — a definition must be "
    "a measurement procedure (e.g. 'unprofitable = gross margin below 5%'), not a synonym. "
    "If the purpose does not fix a threshold or boundary, choose a reasonable one and state "
    "it explicitly; it is a visible, revisable assumption, not a hidden guess. "
    "2) criteria: observable completion criteria on concrete artifacts (files, outputs), "
    "checkable by a third party without asking you. Each criterion is {text, run, expect}: "
    "text describes the condition; when it can be verified by running a command, run is a "
    "command that works in the execution environment stated below (if any) and expect is a "
    "substring that MUST appear in its output — a short ASCII marker the deliverables are "
    "REQUIRED to print (a script that does nothing also exits 0; non-ASCII markers get "
    "corrupted). Leave run/expect empty only when no command can verify it. "
    "3) spec: the detailed task specification to hand to an implementation planner. "
    "Self-contained (repeat the definitions and criteria inside it, including the required "
    "output markers), in the same language as the purpose, naming concrete file "
    "deliverables. Do NOT add work the purpose does not require. "
    "Reply as JSON {definitions:[{term,definition}], criteria:[{text,run,expect}], spec}."
)
_RESPECIFY_SYSTEM = (
    "You revise a specification. Given the PURPOSE, the CURRENT SPEC (JSON) and FEEDBACK "
    "(a concrete gap found in the outcome, or an instruction from the human), produce a "
    "revised full specification addressing the feedback. Keep definitions and criteria "
    "that are still right; change only what the feedback requires. Criteria are "
    "{text, run, expect} — run/expect embed an executable check (see the current spec). "
    "Reply as JSON {definitions:[{term,definition}], criteria:[{text,run,expect}], spec}."
)
_ASSESS_SYSTEM = (
    "You judge whether a PURPOSE (why the work was requested) has been achieved. "
    "You are given the PURPOSE, the SPEC that was adopted for it (its definitions and "
    "criteria were assumptions — question them, do not just re-check them), and EVIDENCE "
    "read directly from the files on disk (existence, size, content excerpts). "
    "Procedure success and purpose achievement are DIFFERENT facts: a script may run, "
    "pass its checks and print 'nothing found' while the purpose is not served (e.g. a "
    "wrong join dropped every row). Judge against the purpose. "
    "Reply achieved='yes' ONLY if the evidence itself shows the purpose is met. "
    "Reply achieved='no' if something concrete is missing or wrong — describe exactly "
    "what in 'gap'. Reply achieved='uncertain' if the evidence cannot settle it or the "
    "judgment needs knowledge you do not have (say what is missing in 'reason'); "
    "NEVER guess: prefer 'uncertain' over an optimistic 'yes'. "
    "Reply as JSON {achieved: 'yes'|'no'|'uncertain', reason, gap}."
)

# 成果物1ファイルあたり証拠として読む上限（LLM 文脈の肥大を防ぐ）。
# 1200 では通常のコードファイルがほぼ必ず切れ、切れた先への外挿（F1×gemma4）を誘発した。
# 切れた証拠での自律 yes は _assess のコードガードで禁止される（対処3）ため、
# この上限は「ガードが発動する頻度」とのトレードオフになる。
_EVIDENCE_LIMIT = 6000

# 証拠に含める criteria 名指しファイルの抽出（テキストからのファイル名らしき語）。
_FILENAME_RE = re.compile(r"[\w\-./\\]+\.[A-Za-z0-9]{1,5}")


def _auto_review(report: dict) -> dict:
    """既定のレビュー: L4 自身の判定が yes のときだけ受理。uncertain / no は上げる。"""
    return {"accept": report.get("assessment", {}).get("achieved") == "yes", "feedback": ""}


def _noop(_event: Any) -> None:
    pass


class Director:
    """L4。目的を仕様へ変換して L3 に完遂させ、成果を目的に照らして判定する。"""

    def __init__(self, l0: Any, l3: Any = None) -> None:
        self._l0 = l0
        self._l3 = l3 if l3 is not None else Orchestrator(l0)

    def run(
        self,
        model: str,
        purpose: str,
        tools: Sequence[Tool],
        *,
        spec_path: str = "SPEC.md",
        review: Callable[[dict], dict] = _auto_review,
        log: Callable[[Any], None] = _noop,
        system: str | None = None,
        max_rounds: int = 3,
        l3_max: int = 8,
        l2_max: int = 6,
        l2_l1_max: int = 10,
    ) -> dict:
        spec = self._specify(model, purpose, log, system)             # P
        rounds = 0
        result: dict = {}
        assessment: dict = {}
        for _ in range(max_rounds):
            rounds += 1
            _write_spec(spec_path, purpose, spec)                     # 定義の artifact 化
            log(("spec", spec, spec_path))
            result = self._l3.run(                                    # D（Plan 承認は自律）
                model, _l3_goal(spec, spec_path), tools,
                log=log, system=system,
                max_rounds=l3_max, l2_max=l2_max, l2_l1_max=l2_l1_max,
            )
            # C: criteria 埋め込みの check をコード側で実行・照合（verify）。
            # 1つでも落ちれば LLM の assess を経ずに決定的に no（幻覚の余地なし）。
            checks = _run_criteria_checks(spec, tools)
            if checks:
                log(("checks", checks))
            failed = [c for c in checks if c["ok"] is False]
            if failed:
                assessment = {
                    "achieved": "no",
                    "reason": "criteria checks failed (code-side verification)",
                    "gap": "; ".join(
                        f"{c['text']} (check: {c['run']}): {c['detail']}" for c in failed
                    ),
                }
            else:
                assessment = self._assess(model, purpose, spec, result, checks)  # C: 目的判定
            log(("assess", assessment))
            if assessment["achieved"] == "no" and assessment.get("gap") and rounds < max_rounds:
                spec = self._respecify(model, purpose, spec, assessment["gap"], log, system)  # A: 自律
                log(("respec", assessment["gap"]))
                continue
            decision = review(                                        # A: 再帰の底 = 人間
                {"purpose": purpose, "spec": spec, "spec_path": spec_path,
                 "result": result, "assessment": assessment}
            )
            if decision.get("accept"):
                return self._done(True, False, assessment, spec, spec_path, result, rounds)
            feedback = str(decision.get("feedback") or "")
            if not feedback:
                return self._done(False, True, assessment, spec, spec_path, result, rounds)
            spec = self._respecify(model, purpose, spec, feedback, log, system)
            log(("respec", feedback))
        return self._done(False, True, assessment, spec, spec_path, result, rounds)

    @staticmethod
    def _done(achieved, escalated, assessment, spec, spec_path, result, rounds) -> dict:
        return {
            "achieved": achieved, "escalated": escalated, "assessment": assessment,
            "spec": spec, "spec_path": spec_path, "result": result, "rounds": rounds,
        }

    # --- 生命線の LLM 呼び出し（構造化出力） ---
    def _specify(self, model: str, purpose: str, log: Callable, system: str | None = None) -> dict:
        data = self._structured(
            model, _with_env(_SPECIFY_SYSTEM, system), f"PURPOSE:\n{purpose}", _SPECIFY_SCHEMA
        )
        return _normalize_spec(data, purpose, log)

    def _respecify(
        self, model: str, purpose: str, spec: dict, feedback: str, log: Callable,
        system: str | None = None,
    ) -> dict:
        user = (
            f"PURPOSE:\n{purpose}\n\nCURRENT SPEC:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
            f"FEEDBACK:\n{feedback}"
        )
        data = self._structured(model, _with_env(_RESPECIFY_SYSTEM, system), user, _SPECIFY_SCHEMA)
        new = _normalize_spec(data, purpose, log)
        return new if data.get("spec") else spec  # 壊れた改訂で現仕様を失わない

    def _assess(self, model: str, purpose: str, spec: dict, result: dict, checks: list) -> dict:
        evidence, truncated = _evidence(result.get("units", []), spec.get("criteria", []))
        checks_s = "\n".join(
            f"- [{'ok' if c['ok'] else ('SKIPPED' if c['ok'] is None else 'FAILED')}] "
            f"{c['text']} :: {c['detail']}"
            for c in checks
        ) or "(none)"
        user = (
            f"PURPOSE:\n{purpose}\n\n"
            f"SPEC (adopted assumptions):\n{json.dumps(spec, ensure_ascii=False)}\n\n"
            f"CRITERIA CHECKS (executed by code, ground truth):\n{checks_s}\n\n"
            f"EVIDENCE (read from disk):\n{evidence}"
        )
        data = self._structured(model, _ASSESS_SYSTEM, user, _ASSESS_SCHEMA)
        achieved = data.get("achieved")
        if achieved not in ("yes", "no", "uncertain"):
            # 壊れた判定は楽観に倒さない（安全側 = uncertain → 上げる）。
            return {"achieved": "uncertain", "reason": "unparseable assessment", "gap": ""}
        if achieved == "yes" and truncated:
            # 切り詰めた証拠の上の yes は自律では受理しない（コード側ガード。合意005 対処3）。
            # 見えていない部分への外挿は F1×gemma4 で実発火した。人間の受理は review でできる。
            return {
                "achieved": "uncertain",
                "reason": "evidence was truncated; autonomous yes is not allowed on partial "
                          f"evidence (code guard). Model said yes: {str(data.get('reason', ''))[:300]}",
                "gap": str(data.get("gap", "")),
            }
        return {"achieved": achieved, "reason": str(data.get("reason", "")), "gap": str(data.get("gap", ""))}

    def _structured(self, model: str, system: str, user: str, schema: dict) -> dict:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        resp = self._l0.chat(model, messages, format=schema, think=False)
        return _parse_json(resp.message.content)


def _normalize_spec(data: dict, purpose: str, log: Callable) -> dict:
    """specify 応答を仕様 dict に正規化。壊れていたら目的の原文を仕様として使う（劣化を可視化）。"""
    if not data.get("spec"):
        log(("spec_fallback", "specify が壊れたため目的の原文を仕様として使う"))
        return {"definitions": [], "criteria": [], "spec": purpose}
    return {
        "definitions": [
            d for d in data.get("definitions", [])
            if isinstance(d, dict) and d.get("term") and d.get("definition")
        ],
        "criteria": [c for c in map(_normalize_criterion, data.get("criteria", [])) if c],
        "spec": str(data["spec"]),
    }


def _normalize_criterion(c: Any) -> dict | None:
    """criterion を {text, run, expect} に正規化。旧形式（素の文字列）も受ける。"""
    if isinstance(c, str):
        return {"text": c, "run": "", "expect": ""} if c.strip() else None
    if isinstance(c, dict) and str(c.get("text", "")).strip():
        return {
            "text": str(c["text"]),
            "run": str(c.get("run", "") or ""),
            "expect": str(c.get("expect", "") or ""),
        }
    return None


def _run_criteria_checks(spec: dict, tools: Sequence[Tool]) -> list:
    """run を持つ criteria をコード側で実行・照合する（L3 の unit check と同じ形の verify）。"""
    results = []
    for c in spec.get("criteria", []):
        if not c.get("run"):
            continue
        ok, detail = run_check({"run": c["run"], "expect": c.get("expect", "")}, tools)
        results.append({"text": c["text"], "run": c["run"], "ok": ok, "detail": detail})
    return results


def _criterion_line(c: dict) -> str:
    line = c["text"]
    if c.get("run"):
        line += f"（検査: `{c['run']}`"
        if c.get("expect"):
            line += f" → 出力に「{c['expect']}」を含むこと"
        line += "）"
    return line


def _l3_goal(spec: dict, spec_path: str) -> str:
    """L4 の Plan（仕様）を L3 の goal に組む。仕様書ファイルへの参照も渡す。"""
    crits = "\n".join(f"- {_criterion_line(c)}" for c in spec.get("criteria", []))
    parts = [spec["spec"]]
    if crits:
        parts.append(f"完了条件（すべて満たすこと。検査コマンドはコード側で実行される）:\n{crits}")
    parts.append(f"仕様書: {spec_path}（操作的定義を含む。必要なら read_file で参照）")
    return "\n\n".join(parts)


def _write_spec(spec_path: str, purpose: str, spec: dict) -> None:
    """仕様を artifact に書く。L3/L2 も参照でき、人間も直接直せる（ファイル・グラウンディング）。"""
    defs = "\n".join(f"- **{d['term']}**: {d['definition']}" for d in spec.get("definitions", []))
    crits = "\n".join(f"- [ ] {_criterion_line(c)}" for c in spec.get("criteria", []))
    text = (
        "# SPEC — L4 が目的から定めた仕様\n"
        "（L4 の生成物。定義・完了条件は仮定を含む。直接編集して直してよい）\n\n"
        f"## 目的（人間の入力・原文）\n{purpose}\n\n"
        f"## 操作的定義\n{defs or '(なし)'}\n\n"
        f"## 完了条件\n{crits or '(なし)'}\n\n"
        f"## 仕様（L3 への入力）\n{spec.get('spec', '')}\n"
    )
    p = Path(spec_path)
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _evidence(units: list, criteria: list, limit: int = _EVIDENCE_LIMIT) -> tuple[str, bool]:
    """成果物ファイルをディスクから読み直して証拠に組む。done フラグ（表象）は信用しない。

    units のファイルに加え、criteria が名指しするファイルと workdir の一覧も含める
    （対処2 — 完了条件の対象が plan の units に現れないことがある。sales×gemma4 で実発火）。
    返り値: (証拠テキスト, どこかで切り詰めたか)。切り詰めがあると自律 yes は禁止される。
    """
    paths: list[str] = []
    for u in units:
        path = str(u.get("file") or "")
        if path and path not in paths:
            paths.append(path)
    mentioned = " ".join(
        f"{c.get('text', '')} {c.get('run', '')} {c.get('expect', '')}" for c in criteria
    )
    for m in _FILENAME_RE.findall(mentioned):
        if m not in paths and Path(m).is_file():
            paths.append(m)

    unit_files = {str(u.get("file") or "") for u in units}
    truncated = False
    parts = []
    listing = sorted(p.name for p in Path(".").iterdir() if p.is_file())
    parts.append("workdir files: " + (", ".join(listing[:40]) or "(empty)"))
    for path in paths:
        p = Path(path)
        origin = "unit deliverable" if path in unit_files else "named in criteria"
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            if len(text) > limit:
                truncated = True
                excerpt = text[:limit] + f"\n...(truncated, {len(text)} chars total)"
            else:
                excerpt = text
            parts.append(f"--- {path} (exists on disk, {p.stat().st_size} bytes, {origin}) ---\n{excerpt}")
        else:
            parts.append(f"--- {path} (MISSING on disk, {origin}) ---")
    if len(parts) == 1:
        parts.append("(no deliverables)")
    return "\n".join(parts), truncated
