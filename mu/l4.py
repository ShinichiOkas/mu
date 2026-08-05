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
import re
from pathlib import Path
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l3 import Orchestrator, _parse_json, _with_env, run_check  # 層間共用ヘルパ
from .role_kb import role_prompt, role_section, role_tools, task_roles

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

_DEFAULT_QA_TASK = {
    "role": "qa",
    "task": "受け入れ基準に照らして成果物を独立に検証し、判定書を書く",
    "file": "verdict.md",
    "criterion": "判定書の1行目が『ACHIEVED: 』で始まる",
}

_VERDICT_REQUIREMENT = "判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む"

_VERDICT_CONTRACT = (
    "判定書の書式（機械的に読まれる。厳守）:\n"
    "ACHIEVED: yes|no|uncertain\n"
    "REASON: <1〜3行。確認した証拠を挙げる>\n"
    "GAP: <no のとき何が欠けているか。yes/uncertain のときは空でよい>"
)

_PROCESS_NOTE = "（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）"



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
            _write_process(process_path, purpose, tasks, _process_note(roles))
            log(("process", tasks, process_path))

            failure = self._execute(model, tasks, tools, roles, pool,   # D（役割を着た L3 の逐次ループ）
                                    spec_path, purpose, system, log, limits)
            checks = _run_criteria_checks(spec, tools)                  # C（決定論の床）
            if checks:
                log(("checks", checks))
            verdict = _read_verdict(tasks) if failure is None else None  # C（QA の判定を機械読み）
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
                    _invalidate(tasks, decision.get("invalidate", []))
                    continue
                if act == "replan":
                    new = self._process(model, spec, roles, pool, log, system)
                    tasks = _carry_done_tasks(tasks, new)
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
        return _normalize_tasks(data.get("tasks", []), task_roles(roles), log)

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
            f"PROCESS:\n{_process_summary(tasks)}\n\n"
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
_DEFAULT_QA_TASK = {
    "role": "qa",
    "task": "受け入れ基準に照らして成果物を独立に検証し、判定書を書く",
    "file": "verdict.md",
    "criterion": "判定書の1行目が『ACHIEVED: 』で始まる",
}

# 判定書の書式＝**コードが正規表現で読む契約**（`_read_verdict` と対になる）。
# ポジション側の持ち物なのでコードが供給する。役割定義書に二重に書かせない（合意008）。
_VERDICT_REQUIREMENT = "判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む"
_VERDICT_CONTRACT = (
    "判定書の書式（機械的に読まれる。厳守）:\n"
    "ACHIEVED: yes|no|uncertain\n"
    "REASON: <1〜3行。確認した証拠を挙げる>\n"
    "GAP: <no のとき何が欠けているか。yes/uncertain のときは空でよい>"
)

# artifact の注記のミニマム（定義書の `## spec-artifact` / `## process-artifact` で上書き可能）。
_PROCESS_NOTE = "（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）"


def _default_qa_task(roles: dict) -> dict:
    """コードのミニマム定義に、役割定義書の宣言を重ねた QA タスクを作る（合意008）。"""
    doc = roles.get("qa") if isinstance(roles.get("qa"), dict) else {}
    task = dict(_DEFAULT_QA_TASK)
    for key in ("task", "file", "criterion"):
        value = str((doc or {}).get(key, "") or "").strip()
        if value:
            task[key] = value
    return task


def _process_note(roles: dict) -> str:
    """PROCESS.md の注記。定義書の `## process-artifact` があればそれ、無ければミニマム。"""
    return role_section(roles.get("pjm"), "process-artifact") or _PROCESS_NOTE


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
    for t in tasks:                           # 判定書の契約は成功条件にも入れる（床）
        if t["role"] == "qa" and "REASON" not in t["criterion"]:
            t["criterion"] = (t["criterion"] + " / " if t["criterion"] else "") + _VERDICT_REQUIREMENT
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
    m = re.search(r"ACHIEVED\s*:?\s*\**\s*(yes|no|uncertain)\b", text, re.IGNORECASE)
    if not m:
        return {"achieved": "uncertain", "reason": "verdict unparseable (no ACHIEVED line)", "gap": ""}
    return {
        "achieved": m.group(1).lower(),
        "reason": _verdict_field(text, "REASON"),
        "gap": _verdict_field(text, "GAP"),
    }


def _verdict_field(text: str, name: str, limit: int = 600) -> str:
    """判定書の REASON / GAP を読む。1行形式でも Markdown 見出しブロックでも拾う。

    契約はコードが供給するが、書き手は LLM であり装飾（`## REASON` ＋本文）へ流れる
    （008 Phase4 の実走で観測）。**判定語 yes|no|uncertain の厳格さは保ったまま**、
    根拠の文面だけは実体に合わせて頑健に読む——読めないと人間に渡る情報が消えるため。
    """
    inline = re.search(rf"^\W{{0,4}}{name}\s*:\s*(\S.*)$", text, re.M | re.I)
    if inline:
        return inline.group(1).strip()[:limit]
    block = re.search(rf"^#+\s*{name}\s*:?\s*$\n(.+?)(?=^#|\Z)", text, re.M | re.S | re.I)
    if block:
        body = " ".join(line for line in block.group(1).split() if line)
        return body[:limit]
    return ""


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip().lstrip("# ")
    return ""


def _run_criteria_checks(spec: dict, tools: Sequence[Tool]) -> list:
    """run を持つ criteria をコード側で実行・照合する（決定論の床。verdict とは独立）。"""
    results = []
    for c in spec.get("criteria", []):
        if not c.get("run"):
            continue
        ok, detail = run_check({"run": c["run"], "expect": c.get("expect", "")}, tools)
        results.append({"text": c["text"], "run": c["run"], "ok": ok, "detail": detail})
    return results


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
