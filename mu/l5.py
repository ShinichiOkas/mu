"""L5 — 目的の層（PdM / Director）。

人間が自然に言えるのは**目的**であり、詳細な仕様ではない。その落差を埋めるのがこの層。
L4（進行の層）を D として使い、返ってきた検証結果を見て「仕様を直すか・人間に上げるか」を
判断する——L2→L3 と同じ再帰同一構造であり、判断が1段外へ出た形（合意009）。

  P: 目的 → **充足可能性の判断** → 操作的定義＋受入基準＋仕様（SPEC.md）      ← PdM（LLM）
  D: SPEC を L4（PjM）に渡し、プロセスを編ませて完遂させる                    ← 内側の層
  C: L4 が返す verdict（QA の判定）と checks（決定論の受入検査）を読む         ← コード
  A: accept / respec（仕様を直して再実行）/ escalate（人間へ）                ← レビュー担当

決定論の床（この層）:
  - PdM が「充足不能」と申告したら**仕様を作らせず人間へ上げる**（合意007。矛盾の独断解決を塞ぐ）
  - 入力の実物（一覧＋先頭抜粋）はコードが読んで PdM に前置する（形式を発明させない）
  - 壊れた specify 応答は目的の原文を仕様として使う（劣化を可視化して進む）
  - L4 が「自分の職掌では直せない（respec / escalate）」と返したときだけ、この層が動く

やり方（PdM のプロンプト）は roles/pdm.md にあり、コードには無い。返すべき形はスキーマが
唯一の出所（合意008）。**無状態** — 上限・レビュー担当・役割 KB・モデルプールは呼び出し側が規定する。
人間はモデルプールの外にいる（escalate で依頼する相手。再帰の底）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l3 import structured
from .l4 import Manager, lifeline_system
from .role_kb import role_section

# --- スキーマ（ポジションの契約。コードの分岐が依存する） ----------------------

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
        "feasible": {"type": "boolean"},
        "conflicts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["definitions", "criteria", "spec", "feasible", "conflicts"],
}

_SPEC_NOTE = "（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）"



_NO_VERDICT = {"achieved": "uncertain", "reason": "no verdict (QA task not completed)", "gap": ""}


def _with_check_facts(reason: str, checks: list) -> str:
    """respec の FEEDBACK に、落ちた受入検査の**事実**（コマンドと実際の出力）を添える。"""
    failed = [c for c in (checks or []) if c.get("ok") is False]
    if not failed:
        return reason
    facts = "\n".join(f"  検査: {c['run']}\n  実際: {c['detail']}" for c in failed)
    return f"{reason}\n\n落ちた受入検査（コードが実行した事実）:\n{facts}"


def _noop(_event: Any) -> None:
    pass


def _done(achieved, escalated, assessment, spec, spec_path, tasks, process_path, rounds,
          l4_rounds: int = 0, escalation_reason: str = "") -> dict:
    """呼び出し側への返り値。`rounds` は**この層の**周回（respec サイクル）、
    `l4_rounds` は最後に回した L4（PjM サイクル）の周回——予算は各層が自分で持つ（合意009）。

    `escalation_reason`（合意021 修正③）: escalate で返すとき、**なぜ落ちたか**を機械契約に
    載せる。021 schedule で「achieved: false なのに assessment は yes」となり、下の層の
    escalate 理由（検査コマンドの故障）が最終結果から読めなかった。
    """
    return {
        "achieved": achieved, "escalated": escalated, "assessment": assessment,
        "spec": spec, "spec_path": spec_path, "tasks": tasks,
        "process_path": process_path, "rounds": rounds, "l4_rounds": l4_rounds,
        "escalation_reason": escalation_reason,
    }


# 自己記述を全文見せるスクリプト。抜粋（先頭5行）では usage が途中で切れ、PdM が続きの
# サブコマンドを推測で発明する（021 schedule: `list` を2走連続で発明 → 検査が壊れ偽・不合格）。
_SCRIPT_SUFFIXES = {".py", ".ps1", ".psm1"}


def _self_description(text: str, suffix: str) -> str:
    """スクリプトの自己記述（.py: 冒頭 docstring / .ps1: 冒頭コメント塊）。無ければ空。"""
    if suffix == ".py":
        stripped = text.lstrip()
        for quote in ('"""', "'''"):
            if stripped.startswith(quote):
                end = stripped.find(quote, len(quote))
                if end != -1:
                    return stripped[len(quote):end].strip()
        return ""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            out.append(s.lstrip("#").strip())
        elif s and not s.lower().startswith("param"):
            break
    return "\n".join(out).strip()


def _input_grounding(workdir: str, exclude: set, max_files: int = 12, head: int = 300) -> str:
    """作業ディレクトリの**実在する入力**を一覧＋抜粋にして返す（合意007 C2）。

    PdM は目的の文章だけからは入力の形式を知りえず、実測すると形式を発明する
    （sales×12b: ヘッダーを2度発明 → 不一致 → respec → 入力破壊）。仕様を作る前に
    実物を前置する。005 の assess 証拠グラウンディング・006 の env preamble と同型で、
    「事実は呼び出し側（コード）が渡し、LLM に想像させない」形。

    スクリプト（実行可能な道具）は先頭5行でなく**自己記述（docstring/コメント塊）を全文**
    見せる（合意021 修正②）。見えない usage の続きは推測で発明される——規範で禁じると同時に、
    推測の必要そのものを消す。
    """
    p = Path(workdir or ".")
    if not p.is_dir():
        return ""
    entries = [f for f in sorted(p.iterdir()) if f.name not in exclude and not f.name.startswith(".")]
    lines = []
    for f in entries[:max_files]:
        if f.is_dir():
            lines.append(f"- {f.name}/ (directory)")
            continue
        is_script = f.suffix.lower() in _SCRIPT_SUFFIXES
        try:
            size = f.stat().st_size
            with f.open(encoding="utf-8", errors="strict") as fh:
                text = fh.read(4000 if is_script else head)
        except (OSError, UnicodeDecodeError):
            lines.append(f"- {f.name} (binary or unreadable)")
            continue
        doc = _self_description(text, f.suffix.lower()) if is_script else ""
        if doc:
            lines.append(
                f"- {f.name} ({size} bytes) — 自己記述（スクリプト冒頭の説明。"
                "コマンド・引数はここに書かれた形だけを使うこと）:"
            )
            lines.extend(f"    {line}" for line in doc.splitlines()[:40])
            continue
        lines.append(f"- {f.name} ({size} bytes) — 先頭:")
        lines.extend(f"    {line}" for line in text.splitlines()[:5])
    if len(entries) > max_files:
        lines.append(f"- （他 {len(entries) - max_files} 件）")
    return "\n".join(lines)


def _inputs_block(inputs: str) -> str:
    if not inputs:
        return ""
    return (
        "\n\nEXISTING FILES IN THE WORK DIRECTORY (the real inputs, read from disk):\n"
        f"{inputs}"
    )


def _infeasible(spec: dict) -> bool:
    """PdM が明示的に「充足不能」と申告したか。欠落・True はどちらも「進める」（合意007 決定4）。"""
    return spec.get("feasible") is False


def _auto_review(report: dict) -> dict:
    """既定のレビュー: ラウンドが完全に ok（全タスク done・check 全通過・verdict yes）のときだけ受理。"""
    return {"accept": bool(report.get("ok")), "feedback": ""}


def _spec_note(roles: dict) -> str:
    """SPEC.md の注記。定義書の `## spec-artifact` があればそれ、無ければコードのミニマム。"""
    return role_section(roles.get("pdm"), "spec-artifact") or _SPEC_NOTE


def _normalize_spec(data: dict, purpose: str, log: Callable) -> dict:
    """specify 応答を仕様 dict に正規化。壊れていたら目的の原文を仕様として使う（劣化を可視化）。

    合意007: `feasible` / `conflicts`（PdM の充足可能性の申告）も持ち回る。
    **欠落は feasible=True 扱い**——申告できないモデルで常に止まると自律の到達距離を
    測れなくなるため、明示的な false だけを escalate の分岐条件にする。
    """
    feasible = False if data.get("feasible") is False else True
    conflicts = [str(c).strip() for c in (data.get("conflicts") or []) if str(c).strip()]
    if not data.get("spec"):
        if feasible:  # 充足不能の申告時は spec が空でも壊れではない（仕様を作らないのが正しい）
            log(("spec_fallback", "specify が壊れたため目的の原文を仕様として使う"))
        return {
            "definitions": [], "criteria": [], "spec": "" if not feasible else purpose,
            "feasible": feasible, "conflicts": conflicts,
        }
    return {
        "definitions": [
            d for d in data.get("definitions", [])
            if isinstance(d, dict) and d.get("term") and d.get("definition")
        ],
        "criteria": [c for c in map(_normalize_criterion, data.get("criteria", [])) if c],
        "spec": str(data["spec"]),
        "feasible": feasible,
        "conflicts": conflicts,
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


def _criterion_line(c: dict) -> str:
    line = c["text"]
    if c.get("run"):
        line += f"（検査: `{c['run']}`"
        if c.get("expect"):
            line += f" → 出力に「{c['expect']}」を含むこと"
        line += "）"
    return line


def _write_spec(spec_path: str, purpose: str, spec: dict, note: str = "") -> None:
    """仕様を artifact に書く。全タスクが参照でき、人間も直接直せる（ファイル・グラウンディング）。"""
    defs = "\n".join(f"- **{d['term']}**: {d['definition']}" for d in spec.get("definitions", []))
    # 受入基準は**番号付き**で書く。判定書はこの番号で項目ごとの合否を返す契約になっており
    # （合意017）、番号が無いと QA と機械が同じ項目を指せない。
    crits = "\n".join(
        f"{i}. [ ] {_criterion_line(c)}" for i, c in enumerate(spec.get("criteria", []), 1)
    )
    infeasible = ""
    if _infeasible(spec):
        conflicts = "\n".join(f"- {c}" for c in spec.get("conflicts", [])) or "- （申告なし）"
        infeasible = (
            "## 充足不能の申告（PdM）\n"
            "この目的は制約が同時に満たせないと判断された。**仕様は作られていない**——"
            "制約を弱めた仕様や退化解を独断で採らず、人間の判断を待つ（合意007）。\n"
            f"{conflicts}\n\n"
        )
    text = (
        "# SPEC — L5（PdM）が目的から定めた仕様\n"
        f"{note or _SPEC_NOTE}\n\n"
        f"## 目的（人間の入力・原文）\n{purpose}\n\n"
        f"{infeasible}"
        f"## 操作的定義\n{defs or '(なし)'}\n\n"
        f"## 受入基準\n{crits or '(なし)'}\n\n"
        f"## 仕様\n{spec.get('spec', '')}\n"
    )
    p = Path(spec_path)
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class Director:
    """L5。目的を仕様に翻訳し、L4（進行の層）を回し、結果を見て次の一手を決める。"""

    def __init__(self, l0: Any, l4: Any = None) -> None:
        self._l0 = l0
        self._l4 = l4 if l4 is not None else Manager(l0)

    def run(
        self,
        model: str,
        purpose: str,
        tools: Sequence[Tool],
        *,
        roles: dict | None = None,
        models: Sequence[str] | None = None,
        spec_path: str = "SPEC.md",
        process_path: str = "PROCESS.md",
        review: Callable[[dict], dict] = _auto_review,
        log: Callable[[Any], None] = _noop,
        system: str | None = None,
        max_rounds: int = 2,
        l4_max: int = 3,
        l3_max: int = 8,
        l2_max: int = 6,
        l2_l1_max: int = 10,
        guard: Any = None,
        deadline: Any = None,
        protected: Sequence[str] | None = None,
    ) -> dict:
        roles = roles or {}
        inputs = _input_grounding(                                    # 入力の実物（合意007 C2）
            str(Path(spec_path).parent), {Path(spec_path).name, Path(process_path).name}
        )
        if inputs:
            log(("inputs", inputs))
        spec = self._specify(model, purpose, roles, log, system, inputs)
        if _infeasible(spec):                                         # 充足不能なら人間へ（合意007）
            return self._stop_infeasible(purpose, spec, spec_path, process_path, [], 0, roles, log)

        rounds, l4_rounds, tasks, assessment = 0, 0, [], _NO_VERDICT
        for _ in range(max_rounds):
            rounds += 1
            # 締切（呼び出し側注入・合意018 ⑥）。外部 kill は finally を飛ばし観測ゼロを
            # 生む——時間切れは部分結果つきの escalate として**正常に返す**。
            if deadline and deadline():
                assessment = {
                    "achieved": "uncertain",
                    "reason": "時間予算を使い切った（deadline）。部分結果で停止。人間の判断が要る",
                    "gap": "",
                }
                return _done(False, True, assessment, spec, spec_path, tasks,
                             process_path, rounds, l4_rounds,
                             escalation_reason="時間予算を使い切った（deadline）")
            _write_spec(spec_path, purpose, spec, _spec_note(roles))
            log(("spec", spec, spec_path))

            outcome = self._l4.run(                                   # D: 進行の層に任せる
                model, spec, tools, roles=roles, models=models, purpose=purpose,
                spec_path=spec_path, process_path=process_path, log=log, system=system,
                guard=guard, deadline=deadline, protected=protected,
                # ↑ 破れ検査・締切・保護一覧は呼び出し側が注入し、この層は素通しする
                max_rounds=l4_max, l3_max=l3_max, l2_max=l2_max, l2_l1_max=l2_l1_max,
            )
            tasks = outcome["tasks"]
            l4_rounds = outcome["rounds"]
            assessment = outcome["verdict"] or _NO_VERDICT
            report = {
                "purpose": purpose, "spec": spec, "spec_path": spec_path,
                "tasks": tasks, "process_path": process_path,
                "assessment": assessment, "checks": outcome["checks"], "ok": outcome["ok"],
            }
            # PjM が「自分の職掌では直せない」と言い、まだ予算があるなら仕様を直して再実行する。
            if outcome["outcome"] == "respec" and rounds < max_rounds:
                # PjM の言葉（判断）に、落ちた検査の**事実**を添える。仕様のどこが実行不能だったかは
                # 解釈でなく実行結果に出ている（合意014 A）。
                spec = self._respecify(
                    model, purpose, spec, _with_check_facts(outcome["reason"], outcome["checks"]),
                    roles, log, system, inputs,
                )
                if _infeasible(spec):
                    return self._stop_infeasible(
                        purpose, spec, spec_path, process_path, tasks, rounds, roles, log
                    )
                continue

            decision = review(report)                                  # A: 判断は外へ（既定は自動）
            if decision.get("accept"):
                return _done(True, False, assessment, spec, spec_path, tasks, process_path, rounds, l4_rounds)
            feedback = str(decision.get("feedback") or "")
            if not feedback:
                # 受理されず指示も無い＝人間へ。下の層の申告理由を結果契約で持ち上げる（修正③）。
                return _done(False, True, assessment, spec, spec_path, tasks, process_path,
                             rounds, l4_rounds, escalation_reason=str(outcome.get("reason") or ""))
            spec = self._respecify(model, purpose, spec, feedback, roles, log, system, inputs)
            if _infeasible(spec):
                return self._stop_infeasible(
                    purpose, spec, spec_path, process_path, tasks, rounds, roles, log
                )

        return _done(False, True, assessment, spec, spec_path, tasks, process_path, rounds,
                     l4_rounds, escalation_reason="respec 予算切れ（この層の周回を使い切った）")

    def _stop_infeasible(
        self, purpose: str, spec: dict, spec_path: str, process_path: str,
        tasks: list, rounds: int, roles: dict, log: Callable,
    ) -> dict:
        """PdM が「目的は充足不能」と申告したとき、仕様を作らせず人間へ上げる（合意007 C1-(d)）。

        H3 の観測（矛盾を検出しながら退化解を独断採用し全層が忠実に「達成」した）への対処。
        判断（矛盾か否か）は LLM、**握り潰させない分岐はここ（コードの決定論）**。
        申告は SPEC.md にも残す——観測を殺さないガードにするため（合意007 決定4）。
        """
        _write_spec(spec_path, purpose, spec, _spec_note(roles))
        conflicts = spec.get("conflicts") or []
        log(("infeasible", conflicts))
        assessment = {
            "achieved": "uncertain",
            "reason": "PdM が目的を充足不能と申告した（制約が同時に満たせない）。人間の判断が要る",
            "gap": "; ".join(conflicts),
        }
        return _done(False, True, assessment, spec, spec_path, tasks, process_path, rounds,
                     escalation_reason="PdM が目的を充足不能と申告した")

    # --- 生命線の LLM 呼び出し（やり方は roles/pdm.md、形はスキーマ） ---
    def _specify(
        self, model: str, purpose: str, roles: dict, log: Callable,
        system: str | None = None, inputs: str = "",
    ) -> dict:
        data = structured(
            self._l0, model,
            lifeline_system(roles, "pdm", "specify", _SPECIFY_SCHEMA, system, log),
            f"PURPOSE:\n{purpose}{_inputs_block(inputs)}", _SPECIFY_SCHEMA,
        )
        return _normalize_spec(data, purpose, log)

    def _respecify(
        self, model: str, purpose: str, spec: dict, feedback: str, roles: dict, log: Callable,
        system: str | None = None, inputs: str = "",
    ) -> dict:
        user = (
            f"PURPOSE:\n{purpose}{_inputs_block(inputs)}\n\n"
            f"CURRENT SPEC:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
            f"FEEDBACK:\n{feedback}"
        )
        log(("respec", feedback))
        data = structured(
            self._l0, model,
            lifeline_system(roles, "pdm", "respecify", _SPECIFY_SCHEMA, system, log),
            user, _SPECIFY_SCHEMA,
        )
        new = _normalize_spec(data, purpose, log)
        if _infeasible(new):
            return new  # 充足不能の申告は spec 本文が空でも「壊れ」ではない（合意007）
        return new if data.get("spec") else spec  # 壊れた改訂で現仕様を失わない
