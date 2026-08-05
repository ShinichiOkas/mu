"""L4 — 目的の層（PdM + PjM / Director）。

人間が自然に言えるのは目的であり、詳細な仕様ではない。その落差を埋めるのが
この層（合意005）。合意006 で、単一の会話ではなく**役割注釈付きプロセス**として
仕事を編む形に拡張された。マルチエージェントは新しいフレームワークではなく、
「役割を着せた L3 の逐次ループ」であり、並列化は後から足せる最適化にすぎない。
合意007 で、確率の問題が判定から**定義の作り方**へ移ったことへの対処が入った——
仕様を作る前に「作ってよいか（充足可能か）」を問い、入力の実物に接地する。

役割分担（合意006／007。各役割の定義書 roles/*.md は PjM に渡されるナレッジベースであり、
その frontmatter は**権限の宣言**でもある）:
  PdM : 目的 → まず**充足可能性の申告**（制約が同時に満たせないなら仕様を作らない）、
        可能なら操作的定義＋受入基準＋仕様（SPEC.md artifact）。
        定義は目的の文章だけでなく**作業ディレクトリの入力の実物**に接地する ← specify
  PjM : SPEC → プロセス（役割注釈付きタスク列）を編み、人選（モデル割当）し、
        失敗や verdict を受けて**部分再実行**（どのタスクを無効化するか）を判断 ← LLM 判断
  実行: プロセスの1タスクずつを、役割定義を system に前置し**役割の権限で絞ったツール**を
        渡した L3 が完遂                                                  ← コードのループ
  QA  : プロセス末尾の独立タスク。SPEC・実物・**目的の原文**を見て verdict.md を書く。
        目的の達成（原文の制約が守られたか）と仕様への忠実さは別物であり、
        その差を検査できるのは原文を持つ QA だけ。
        L4 は verdict を機械的に読む（一発 LLM 判定 assess は廃止）

決定論の床（コード側）:
  - PdM が「目的は充足不能」と申告したら仕様を作らせず人間へ上げる（合意007。
    矛盾を検出しながら退化解を独断採用する経路＝H3 をコードで塞ぐ。申告の欠落は「可能」扱い）
  - 入力の実物（一覧＋先頭抜粋）はコードが読んで PdM に前置する（形式を発明させない・合意007）
  - 役割の権限（roles/*.md の frontmatter）はコードが適用する。QA は自分の判定書しか書けず、
    違反は steering エラーで拒否してログに出す（合意007。塞ぐが観測は殺さない）
  - プロセス末尾に QA タスクが無ければ**コードが必ず足す**（検証を飛ばして完遂に到達できない）
  - 部分再実行の依存伝播はコードが行い、**QA タスクは必ず再実行**（done を carry しない）
  - spec の criteria check（実行＋可視マーカー照合）は verdict とは独立に走る
  - 壊れた verdict / 壊れた PjM 判断は安全側（uncertain / escalate）に落ちる

**無状態**。上限（予算の封筒）・レビュー担当・役割 KB・モデルプールは呼び出し側が規定する。
人間はモデルプールの外にいる（PjM が管理する人員ではなく、escalate で依頼する相手。再帰の底）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l3 import Orchestrator, _parse_json, _with_env, run_check  # 層間共用ヘルパ
from .role_kb import role_prompt, role_section, role_tools, task_roles

# --- スキーマ -----------------------------------------------------------------

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
_DEFAULT_QA_TASK = {
    "role": "qa",
    "task": "受け入れ基準に照らして成果物を独立に検証し、判定書を書く",
    "file": "verdict.md",
    "criterion": "判定書の1行目が『ACHIEVED: 』で始まる",
}

# 判定書の書式＝**コードが正規表現で読む契約**（`_read_verdict` と対になる）。
# ポジション側の持ち物なのでコードが供給する。役割定義書に二重に書かせない（合意008）。
_VERDICT_CONTRACT = (
    "判定書の書式（機械的に読まれる。厳守）:\n"
    "ACHIEVED: yes|no|uncertain\n"
    "REASON: <1〜3行。確認した証拠を挙げる>\n"
    "GAP: <no のとき何が欠けているか。yes/uncertain のときは空でよい>"
)

# artifact の注記のミニマム（定義書の `## spec-artifact` / `## process-artifact` で上書き可能）。
_SPEC_NOTE = "（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）"
_PROCESS_NOTE = "（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）"


def _spec_note(roles: dict) -> str:
    """SPEC.md の注記。定義書の `## spec-artifact` があればそれ、無ければコードのミニマム。"""
    return role_section(roles.get("pdm"), "spec-artifact") or _SPEC_NOTE


def _process_note(roles: dict) -> str:
    """PROCESS.md の注記。定義書の `## process-artifact` があればそれ、無ければミニマム。"""
    return role_section(roles.get("pjm"), "process-artifact") or _PROCESS_NOTE


def _default_qa_task(roles: dict) -> dict:
    """コードのミニマム定義に、役割定義書の宣言を重ねた QA タスクを作る（合意008）。"""
    doc = roles.get("qa") if isinstance(roles.get("qa"), dict) else {}
    task = dict(_DEFAULT_QA_TASK)
    for key in ("task", "file", "criterion"):
        value = str((doc or {}).get(key, "") or "").strip()
        if value:
            task[key] = value
    return task


def _input_grounding(workdir: str, exclude: set, max_files: int = 12, head: int = 300) -> str:
    """作業ディレクトリの**実在する入力**を一覧＋先頭抜粋にして返す（合意007 C2）。

    PdM は目的の文章だけからは入力の形式を知りえず、実測すると形式を発明する
    （sales×12b: ヘッダーを2度発明 → 不一致 → respec → 入力破壊）。仕様を作る前に
    実物を前置する。005 の assess 証拠グラウンディング・006 の env preamble と同型で、
    「事実は呼び出し側（コード）が渡し、LLM に想像させない」形。
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
        try:
            size = f.stat().st_size
            text = f.read_text(encoding="utf-8", errors="strict")[:head]
        except (OSError, UnicodeDecodeError):
            lines.append(f"- {f.name} (binary or unreadable)")
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


def _noop(_event: Any) -> None:
    pass


class Director:
    """L4。PdM が仕様を定め、PjM がプロセスを編み、役割を着た L3 に1タスクずつ完遂させる。"""

    def __init__(self, l0: Any, l3: Any = None) -> None:
        self._l0 = l0
        self._l3 = l3 if l3 is not None else Orchestrator(l0)

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
        max_rounds: int = 3,
        l3_max: int = 8,
        l2_max: int = 6,
        l2_l1_max: int = 10,
    ) -> dict:
        roles = roles or {}
        pool = list(models) if models else [model]
        limits = {"max_rounds": l3_max, "l2_max": l2_max, "l2_l1_max": l2_l1_max}

        inputs = _input_grounding(                                         # 入力の実物（合意007 C2）
            str(Path(spec_path).parent), {Path(spec_path).name, Path(process_path).name}
        )
        if inputs:
            log(("inputs", inputs))
        spec = self._specify(model, purpose, roles, log, system, inputs)  # PdM
        if _infeasible(spec):                                            # 充足不能なら人間へ（合意007）
            return self._stop_infeasible(purpose, spec, spec_path, process_path, [], 0, roles, log)
        tasks = self._pjm_process(model, spec, roles, pool, log, system)   # PjM: P（体制＝プロセス）
        rounds = 0
        verdict: dict | None = None
        for _ in range(max_rounds):
            rounds += 1
            _write_spec(spec_path, purpose, spec, _spec_note(roles))
            _write_process(process_path, purpose, tasks, _process_note(roles))
            log(("process", tasks, process_path))

            failure = self._execute(model, tasks, tools, roles, pool,      # 役割を着た L3 の逐次ループ
                                    spec_path, purpose, system, log, limits)
            checks = _run_criteria_checks(spec, tools)                     # 決定論の床
            if checks:
                log(("checks", checks))
            verdict = _read_verdict(tasks) if failure is None else None    # QA の判定を機械的に読む
            if verdict:
                log(("verdict", verdict))
            failed_checks = [c for c in checks if c["ok"] is False]
            ok = failure is None and not failed_checks and bool(verdict) and verdict["achieved"] == "yes"

            if not ok:
                decision = self._pjm_decide(                               # PjM: A（部分再実行の判断）
                    model, spec, tasks, failure, failed_checks, verdict, roles, log, system
                )
                act = decision.get("action")
                if rounds < max_rounds:
                    if act == "rerun":
                        _invalidate(tasks, decision.get("invalidate", []))
                        continue
                    if act == "replan":
                        new = self._pjm_process(model, spec, roles, pool, log, system)
                        tasks = _carry_done_tasks(tasks, new)
                        continue
                    if act == "respec":
                        spec = self._respecify(
                            model, purpose, spec, decision.get("reason", ""),
                            roles, log, system, inputs,
                        )
                        if _infeasible(spec):
                            return self._stop_infeasible(
                                purpose, spec, spec_path, process_path, tasks, rounds, roles, log
                            )
                        tasks = self._pjm_process(model, spec, roles, pool, log, system)
                        continue
                # escalate / 壊れた判断 / 予算切れ → 人間の判断へ落ちる

            assessment = verdict or {
                "achieved": "uncertain", "reason": "no verdict (QA task not completed)", "gap": "",
            }
            decision = review({
                "purpose": purpose, "spec": spec, "spec_path": spec_path,
                "tasks": tasks, "process_path": process_path,
                "assessment": assessment, "checks": checks, "ok": ok,
            })
            if decision.get("accept"):
                return self._done(True, False, assessment, spec, spec_path, tasks, process_path, rounds)
            feedback = str(decision.get("feedback") or "")
            if not feedback:
                return self._done(False, True, assessment, spec, spec_path, tasks, process_path, rounds)
            spec = self._respecify(model, purpose, spec, feedback, roles, log, system, inputs)
            if _infeasible(spec):
                return self._stop_infeasible(purpose, spec, spec_path, process_path, tasks, rounds, roles, log)
            tasks = self._pjm_process(model, spec, roles, pool, log, system)

        assessment = verdict or {"achieved": "uncertain", "reason": "rounds exhausted", "gap": ""}
        return self._done(False, True, assessment, spec, spec_path, tasks, process_path, rounds)

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
        return self._done(False, True, assessment, spec, spec_path, tasks, process_path, rounds)

    @staticmethod
    def _done(achieved, escalated, assessment, spec, spec_path, tasks, process_path, rounds) -> dict:
        return {
            "achieved": achieved, "escalated": escalated, "assessment": assessment,
            "spec": spec, "spec_path": spec_path, "tasks": tasks,
            "process_path": process_path, "rounds": rounds,
        }

    # --- 実行ループ（コード・決定論）: 1タスクずつ役割を着せて L3 に完遂させる ---
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
                task_model, _task_goal(t, spec_path, prior, purpose), task_tools,
                log=log, system=task_system or None,
                max_rounds=limits["max_rounds"], l2_max=limits["l2_max"],
                l2_l1_max=limits["l2_l1_max"],
            )
            t["done"] = bool(result.get("done"))
            log(("task_done", t) if t["done"] else ("task_failed", t))
            if not t["done"]:
                return t
        return None

    # --- 生命線の LLM 呼び出し（構造化出力） ---
    #
    # やり方（プロンプト）は roles/*.md から来る。コアが供給するのはポジションの契約
    # （スキーマ由来の形の1行）と呼び出し側の環境だけ（合意008）。
    def _lifeline_system(
        self, roles: dict, role: str, section: str, schema: dict,
        env: str | None, log: Callable,
    ) -> str:
        doc = role_prompt(roles.get(role, ""), section).strip()
        if not doc:
            # 「役割を認識しているが知識が無い状態」＝ミニマム。既定プロンプトで埋めない。
            log(("role_doc_missing", role, section))
        return _with_env("\n\n".join(s for s in (doc, _shape_line(schema)) if s), env)

    def _specify(
        self, model: str, purpose: str, roles: dict, log: Callable,
        system: str | None = None, inputs: str = "",
    ) -> dict:
        data = self._structured(
            model, self._lifeline_system(roles, "pdm", "specify", _SPECIFY_SCHEMA, system, log),
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
        data = self._structured(
            model, self._lifeline_system(roles, "pdm", "respecify", _SPECIFY_SCHEMA, system, log),
            user, _SPECIFY_SCHEMA,
        )
        new = _normalize_spec(data, purpose, log)
        if _infeasible(new):
            return new  # 充足不能の申告は spec 本文が空でも「壊れ」ではない（合意007）
        return new if data.get("spec") else spec  # 壊れた改訂で現仕様を失わない

    def _pjm_process(
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
        data = self._structured(
            model, self._lifeline_system(roles, "pjm", "process", _PROCESS_SCHEMA, system, log),
            user, _PROCESS_SCHEMA,
        )
        return _normalize_tasks(data.get("tasks", []), task_roles(roles), log)

    def _pjm_decide(
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
            f"PROCESS:\n{_process_summary(tasks)}\n\n"
            f"ROUND RESULT:\n" + ("\n".join(result_parts) or "(no info)")
        )
        data = self._structured(
            model, self._lifeline_system(roles, "pjm", "decide", _DECIDE_SCHEMA, system, log),
            user, _DECIDE_SCHEMA,
        )
        if data.get("action") not in ("rerun", "replan", "respec", "escalate"):
            data = {"action": "escalate", "invalidate": [], "reason": "unparseable PjM decision"}
        log(("pjm", data))
        return data

    def _structured(self, model: str, system: str, user: str, schema: dict) -> dict:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        resp = self._l0.chat(model, messages, format=schema, think=False)
        return _parse_json(resp.message.content)


# --- プロセス（役割注釈付きタスク列）のヘルパ ---------------------------------

def _normalize_tasks(raw: list, roles: dict, log: Callable) -> list:
    """PjM 応答をタスク列に正規化する。末尾に QA タスクが無ければコードが必ず足す。"""
    tasks = []
    for t in raw:
        if not isinstance(t, dict):
            continue
        file = str(t.get("file", "")).strip()
        text = str(t.get("task", "")).strip()
        if not file or not text:
            continue
        role = str(t.get("role", "")).strip()
        if roles and role not in roles:
            log(("role_fallback", role, "implementer"))
            role = "implementer"
        task = {
            "role": role, "task": text, "file": file,
            "criterion": str(t.get("criterion", "")), "done": False,
        }
        check = t.get("check") or {}
        if isinstance(check, dict) and (check.get("run") or "").strip():
            task["check"] = {"run": str(check["run"]), "expect": str(check.get("expect", "") or "")}
        if (t.get("model") or "").strip():
            task["model"] = str(t["model"])
        tasks.append(task)
    if not any(t["role"] == "qa" for t in tasks):
        qa = _default_qa_task(roles)          # ミニマム＋定義書の宣言（存在自体は上書き不可）
        log(("qa_appended", qa["file"]))
        tasks.append(dict(qa, done=False))
    return tasks


def _task_goal(task: dict, spec_path: str, prior_files: list, purpose: str = "") -> str:
    goal = (
        f"{task['task']}\n"
        f"役割: {task['role']}\n"
        f"出力ファイル: {task['file']}\n"
        f"成功条件（これを満たすこと）: {task['criterion']}"
    )
    check = task.get("check") or {}
    if check.get("run"):
        goal += f"\n検証コマンド（コード側で実行される）: {check['run']}"
        if check.get("expect"):
            goal += f"\n検証コマンドの出力に必ず含めるべき文字列: {check['expect']}"
    refs = [spec_path, *prior_files]
    goal += f"\n参照できるファイル（read_file で読む）: {', '.join(refs)}"
    if task["role"] == "qa":
        goal += f"\n\n{_VERDICT_CONTRACT}"       # 契約はコードが供給する（合意008）
    if task["role"] == "qa" and purpose:
        # QA だけは目的の原文も見る（合意007 C1-(b)）。SPEC は PdM の生成物であり、
        # 目的の制約を弱めた仕様が下りてくる経路（H3）が実在する。仕様に忠実であることと
        # 目的が達成されたことは別であり、その差を検査できるのは原文を持つ QA だけ。
        goal += (
            f"\n\n目的の原文（PURPOSE。人間が言った言葉。SPEC はこれを PdM が仕様化したもの）:\n{purpose}\n"
            "※ 受入基準の検査に加えて、SPEC が上の目的の制約を弱めていないか"
            "（制約を落とす・言い換えて緩める・退化解を許す）も検査すること。"
            "弱めていれば ACHIEVED: no とし、GAP にその矛盾を書く。"
        )
    return goal


def _invalidate(tasks: list, files: list) -> None:
    """指定ファイルのタスクを無効化し、依存（後続タスクの記述に現れるファイル）へ伝播する。

    QA タスクは必ず無効化する（部分再実行の経路から「検証を飛ばして完遂」に到達させない）。
    判断（どこを無効化するか）は PjM、伝播はここ（コードの決定論）。
    """
    invalid = {str(f).strip() for f in files if str(f).strip()}
    changed = True
    while changed:  # 固定点まで伝播（invalid 集合は単調増加なので停止する）
        changed = False
        for t in tasks:
            if t["file"] in invalid:
                if t.get("done"):
                    t["done"] = False
                    changed = True
                continue
            texts = " ".join([
                t.get("task", ""), t.get("criterion", ""),
                (t.get("check") or {}).get("run", ""), (t.get("check") or {}).get("expect", ""),
            ])
            if any(f in texts for f in invalid):  # 無効化されたファイルに言及＝依存とみなす
                invalid.add(t["file"])
                t["done"] = False
                changed = True
    for t in tasks:
        if t["role"] == "qa":
            t["done"] = False


def _carry_done_tasks(old: list, new: list) -> list:
    """replan 後の done 引き継ぎ。file が両側で一意な非 QA タスクのみ（_carry_done と同じ防御）。

    QA タスクは決して carry しない — 再計画後は必ず検証し直す。
    """
    from collections import Counter
    old_c = Counter(t["file"] for t in old)
    new_c = Counter(t["file"] for t in new)
    done_files = {
        t["file"] for t in old
        if t.get("done") and t["role"] != "qa" and old_c[t["file"]] == 1 and new_c[t["file"]] <= 1
    }
    for t in new:
        if t["role"] != "qa" and t["file"] in done_files:
            t["done"] = True
    return new


def _process_summary(tasks: list) -> str:
    return "\n".join(
        f"- [{'x' if t.get('done') else ' '}] ({t['role']}) {t['file']}: {t['task']}"
        for t in tasks
    )


def _read_verdict(tasks: list) -> dict | None:
    """最後の QA タスクの判定書を機械的に読む。QA 未完なら None、壊れは uncertain（安全側）。"""
    qa = [t for t in tasks if t["role"] == "qa"]
    if not qa or not qa[-1].get("done"):
        return None
    p = Path(qa[-1]["file"])
    if not p.is_file():
        return {"achieved": "uncertain", "reason": f"verdict file missing: {qa[-1]['file']}", "gap": ""}
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"ACHIEVED:\s*(yes|no|uncertain)", text, re.IGNORECASE)
    if not m:
        return {"achieved": "uncertain", "reason": "verdict unparseable (no ACHIEVED line)", "gap": ""}
    reason = re.search(r"REASON:\s*(.+)", text)
    gap = re.search(r"GAP:\s*(.+)", text)
    return {
        "achieved": m.group(1).lower(),
        "reason": reason.group(1).strip() if reason else "",
        "gap": gap.group(1).strip() if gap else "",
    }


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip().lstrip("# ")
    return ""


# --- 仕様（SPEC）のヘルパ（005 から継続） -------------------------------------

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


def _run_criteria_checks(spec: dict, tools: Sequence[Tool]) -> list:
    """run を持つ criteria をコード側で実行・照合する（決定論の床。verdict とは独立）。"""
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


def _write_spec(spec_path: str, purpose: str, spec: dict, note: str = "") -> None:
    """仕様を artifact に書く。全タスクが参照でき、人間も直接直せる（ファイル・グラウンディング）。"""
    defs = "\n".join(f"- **{d['term']}**: {d['definition']}" for d in spec.get("definitions", []))
    crits = "\n".join(f"- [ ] {_criterion_line(c)}" for c in spec.get("criteria", []))
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
        "# SPEC — L4（PdM）が目的から定めた仕様\n"
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


def _write_process(process_path: str, purpose: str, tasks: list, note: str = "") -> None:
    """プロセス（体制表）を artifact に書く。誰が・どの役割で・どのモデルで・何を作るか。"""
    lines = []
    for i, t in enumerate(tasks, 1):
        mark = "x" if t.get("done") else " "
        model = f"（model: {t['model']}）" if t.get("model") else ""
        lines.append(f"{i}. [{mark}] **{t['role']}**{model} → `{t['file']}`")
        lines.append(f"   - task: {t['task']}")
        lines.append(f"   - 成功条件: {t.get('criterion', '')}")
        check = t.get("check") or {}
        if check.get("run"):
            expect = f" → 「{check.get('expect', '')}」" if check.get("expect") else ""
            lines.append(f"   - 検査: `{check['run']}`{expect}")
    text = (
        "# PROCESS — L4（PjM）が編んだプロセス（体制表）\n"
        f"{note or _PROCESS_NOTE}\n\n"
        f"## 目的\n{purpose}\n\n"
        f"## タスク列\n" + "\n".join(lines) + "\n"
    )
    p = Path(process_path)
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
