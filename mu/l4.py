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
from pathlib import Path
from typing import Any, Callable, Sequence

from .l1 import Tool
from .l3 import Orchestrator, noop, run_check, structured, with_env  # 層間共用ヘルパ
from .process import (
    carry_done_tasks, clear_failure, invalidate, normalize_tasks, read_verdict, summarize,
    task_contract, task_goal, unmet_needs, verdict_check, write_process, process_note,
)
from .role_kb import role_perms, role_prompt, role_tools, staffing_lines, task_roles
from .skill_kb import skill_text
from .workspace import copy_in, discard_stale_output, publish, task_tray, tray_tools

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
                    "needs": {"type": "array", "items": {"type": "string"}},
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


def _outcome(outcome, reason, tasks, verdict, checks, ok, rounds, process_path) -> dict:
    """上の層への申告。`outcome` は done / respec / escalate。"""
    return {
        "outcome": outcome, "reason": reason, "tasks": tasks, "verdict": verdict,
        "checks": checks, "ok": ok, "rounds": rounds, "process_path": process_path,
    }


# 時間切れの申告文（合意018 ⑥。L5 も同じ文で申告する——層間共用）。外部 kill は finally を
# 飛ばし観測ゼロを生む——締切は部分結果つきの escalate として**正常に返す**
# （タイムアウトを観測できる失敗に変える）。
TIME_UP = "時間予算を使い切った（deadline）。ここまでの部分結果を返す。人間の判断が要る。"


def _broken_outcome(broken: list, tasks, rounds, process_path, log: Callable) -> dict:
    detail = ", ".join(f"{b.get('path')}({b.get('status')})" for b in broken)
    log(("protection_broken", broken))
    return _outcome(
        "escalate", f"保護された入力が壊れている: {detail}。"
        "壊れた入力の上で作業を続けても結果は意味を持たない。人間の確認が要る。",
        tasks, None, [], False, rounds, process_path,
    )


def plan_lint(task: dict, doc: Any, protected: Sequence[str] | None, log: Callable) -> Callable:
    """L3 の Plan をコードが検査する承認スロット（合意018 ④⑤）。

    017 実走: Planner は役割の write_scope の外の成果物（read_verification_log.txt）や、
    保護入力に触れる単位を発明した。規範（プロンプト）は確率的にしか効かない——
    単位の `file` は計画の時点でコードが拒否する:
      - 保護された入力を file にする単位（直接の再作成。スクリプト経由の間接破壊は
        ACL 層と guard が止める）
      - write_scope=own の役割で、タスクの出力ファイル以外を file にする単位
    全滅したらタスク自身を1単位として置く（空の計画は L3 が「empty plan」で失敗し、
    タスクごと死ぬため）。
    """
    guarded = {str(Path(p).resolve()) for p in (protected or [])}
    _, scope = role_perms(doc)
    own = str(Path(task["file"]).resolve())
    has_contract = bool(task_contract(task))   # 契約持ち（QA）の成果物は検査もコードが決める

    def approve(units: list) -> list:
        kept = []
        for u in units:
            f = str(u.get("file") or "")
            resolved = str(Path(f).resolve()) if f else ""
            if resolved and resolved in guarded:
                log(("unit_rejected", task["role"], f, "保護された入力ファイル"))
                continue
            if scope == "own" and resolved and resolved != own:
                log(("unit_rejected", task["role"], f, f"write_scope 外（書けるのは {task['file']} のみ）"))
                continue
            # 判定書 unit の検査は正準（コード供給）に差し替える。LLM が発明した検査は
            # それ自体が壊れて正しい判定書を落とす（019p4 で3回実発火）。
            if has_contract and resolved == own:
                u = dict(u, check=verdict_check(task["file"]))
            kept.append(u)
        if not kept:
            log(("plan_fallback", task["role"], task["file"]))
            kept = [{
                "task": task["task"], "file": task["file"],
                "criterion": task.get("criterion", ""), "done": False,
            }]
            if has_contract:
                kept[0]["check"] = verdict_check(task["file"])
        return kept

    return approve


# --- 層をまたいで使う生命線のヘルパ（L5 も同じ形で LLM に判断させる） ----------

def lifeline_system(
    roles: dict, role: str, section: str, schema: dict, env: str | None, log: Callable,
    skills: dict | None = None,
) -> str:
    """役割定義（やり方）＋装備（skill）＋スキーマ由来の契約（形）＋環境 で system を組む。

    定義書が無ければ「役割は認識しているが知識が無い」状態になる——既定プロンプトで
    埋めず、その事実をログに出す（合意008）。

    ポジション（pdm / pjm / director）にも skill が装着される（合意029）。プロジェクト側の
    skill が確実に名指しできるのは**名前が動かない4ポジション**であり、そこに pdm / pjm が
    含まれる以上、生命線の side でも着せなければ `applies_to: pdm` が空手形になる。
    """
    doc = role_prompt(roles.get(role, ""), section).strip()
    if not doc:
        log(("role_doc_missing", role, section))
    equipped = skill_text(skills or {}, role, log)
    return with_env("\n\n".join(s for s in (doc, equipped, _shape_line(schema)) if s), env)


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
        skills: dict | None = None,
        models: Sequence[str] | None = None,
        purpose: str = "",
        spec_path: str = "SPEC.md",
        process_path: str = "PROCESS.md",
        log: Callable[[Any], None] = noop,
        system: str | None = None,
        guard: Callable[[], list] | None = None,
        deadline: Callable[[], bool] | None = None,
        protected: Sequence[str] | None = None,
        workspace: str | None = None,
        max_rounds: int = 3,
        l3_max: int = 8,
        l2_max: int = 6,
        l2_l1_max: int = 10,
    ) -> dict:
        """SPEC を完遂まで進める。返り値の `outcome` が上の層への申告:

            done     — 受入基準・verdict とも通った
            respec   — 仕様が悪いと PjM が判断した（この層では直せない）
            escalate — 人手が要る／予算が尽きた

        `workspace` を渡すと、各タスクは自分の tray（作業区画）で走る（合意030。
        copy-in / publish-out・ツールの閉じ込め・single-writer の発行ゲート）。
        None なら従来どおり共有 cwd で走る——隔離は呼び出し側が規定する環境接地であり、
        guard / protected / deadline と同じ注入の型。
        """
        roles = roles or {}
        skills = skills or {}
        pool = list(models) if models else [model]
        limits = {"max_rounds": l3_max, "l2_max": l2_max, "l2_l1_max": l2_l1_max}

        tasks = self._process(model, spec, roles, pool, log, system, skills)   # P（体制＝プロセス）
        rounds = 0
        for _ in range(max_rounds):
            rounds += 1
            # 締切（呼び出し側注入・合意018 ⑥）。層の予算は周回数建てで壁時計と整合しない——
            # 外部 kill は finally を飛ばし観測ゼロを生むため、時間切れは部分結果つきで返す。
            if deadline and deadline():
                return _outcome("escalate", TIME_UP, tasks, None, [], False, rounds, process_path)
            # 守られるべき入力（原本）が壊れていないかを**周の頭で**見る。壊れた後の作業は
            # すべて偽の前提の上に乗るため、進める意味がない（合意016 ②。015 で実発火）。
            # 保護機構そのものは持たない——呼び出し側が注入する（環境接地は caller の責務）。
            broken = guard() if guard else []
            if broken:
                return _broken_outcome(broken, tasks, rounds, process_path, log)
            write_process(process_path, purpose, tasks, process_note(roles))
            log(("process", tasks, process_path))

            failure, broken, timed_out = self._execute(                 # D（役割を着た L3 の逐次ループ）
                model, tasks, tools, roles, pool,
                spec_path, purpose, system, log, limits,
                guard=guard, deadline=deadline, protected=protected, skills=skills,
                workspace=workspace,
            )
            if broken:      # タスク境界の検査で破れが出た（017: 1周が締切に収まらず周頭では遅い）
                return _broken_outcome(broken, tasks, rounds, process_path, log)
            if timed_out:
                return _outcome("escalate", TIME_UP, tasks, None, [], False, rounds, process_path)
            checks = _run_criteria_checks(spec, tools)                  # C（決定論の床）
            if checks:
                log(("checks", checks))
            # C: QA の判定を機械読み。**集約はコード側**（全項目 PASS のみ達成。合意017）。
            verdict = read_verdict(tasks, spec.get("criteria", [])) if failure is None else None
            if verdict:
                log(("verdict", verdict))
            failed_checks = [c for c in checks if c["ok"] is False]
            ok = failure is None and not failed_checks and bool(verdict) and verdict["achieved"] == "yes"
            if ok:
                return _outcome("done", "", tasks, verdict, checks, True, rounds, process_path)

            decision = self._decide(                                    # A（部分再実行の判断）
                model, spec, tasks, failure, failed_checks, verdict, roles, log, system, skills
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
        guard: Callable[[], list] | None = None,
        deadline: Callable[[], bool] | None = None,
        protected: Sequence[str] | None = None,
        skills: dict | None = None,
        workspace: str | None = None,
    ) -> tuple[dict | None, list, bool]:
        """pending タスクを順に実行する。返り値は (最初に失敗したタスク | None, 破れ, 時間切れ)。

        guard / deadline は**タスク境界でも**見る（合意018 ③⑥）。017 再走では1周が締切に
        収まらず、周の頭だけの検査は一度も走らなかった——破壊はタスクの中で起きる。

        `workspace` があれば各タスクは tray で走る（合意030）: needs＋SPEC を写して開始し、
        ツールを tray に閉じ、完了時に宣言された出力だけを共有空間へ発行する。発行の
        所有権ゲート（single-writer）で拒否されたタスクは、正直な失敗として PjM に乗る。
        """
        for i, t in enumerate(tasks):
            if t.get("done"):
                continue
            if deadline and deadline():
                return None, [], True
            broken = guard() if guard else []
            if broken:
                return None, broken, False
            # needs のゲート（合意030: 満たせなければタスクは実行できない）。内部依存は
            # 産出タスクの done、外部ファイルは実在で見る。満たせないタスクは L3 に渡さず、
            # コードが確認した事実を載せて正直に失敗させる——PjM の decide に乗る。
            producers = {p["file"]: bool(p.get("done")) for p in tasks[:i]}
            missing = unmet_needs(t, producers)
            if missing:
                t["last_failure"] = (
                    f"needs 未充足（コードが確認した事実）: {', '.join(missing)} が無い"
                    "（先行タスクが産出していないか、外部ファイルの名前が違う）"
                )
                log(("needs_unmet", t["file"], missing))
                return t, [], False
            doc = roles.get(t["role"], "")
            # tray（合意030）: needs＋SPEC を写して開始し、ツールを tray に閉じる。
            # 未宣言の入力は tray に無い＝読めずに正直に失敗する（グラフは構成的に真）。
            tray = None
            if workspace:
                tray = task_tray(workspace, t["role"], i)
                discard_stale_output(tray, t["file"])   # 前回試行の残骸を発行させない
                missing_in = copy_in(tray, t["needs"])
                if missing_in:
                    t["last_failure"] = (
                        f"入力を作業区画へ写せない（コードが確認した事実）: {', '.join(missing_in)}"
                    )
                    log(("copy_in_missing", t["file"], missing_in))
                    return t, [], False
                if Path(spec_path).is_file():
                    copy_in(tray, [spec_path])
            # 契約（判定書の書式等）は system にも載せる。goal だけだと L3 の再計画の転記から
            # 欠落して L2 に届かない（019 実走）。system はコードが素通しで運ぶ。
            # 装備（skill）は職掌の直後・契約の手前に入る（合意029）——契約と環境は後ろの
            # ままにする（019 で確立した「再計画で薄まらない経路」の順序を動かさない）。
            tray_env = (
                f"作業ディレクトリ: {tray}（このタスク専用。参照ファイルは写しが置かれている。"
                f"相対パスで読み書きし、成果物 {t['file']} をここに書けば完了時にコードが"
                "共有空間へ発行する）"
            ) if tray else ""
            task_system = "\n\n".join(
                s for s in (role_prompt(doc), skill_text(skills or {}, t["role"], log),
                            task_contract(t), system, tray_env) if s
            )
            task_model = t.get("model") if t.get("model") in pool else model
            base_tools = tray_tools(tools, tray, log) if tray else tools
            task_tools = role_tools(base_tools, doc, t["file"], t["role"], log)  # 役割別の権限（B1）
            result = self._l3.run(
                task_model, task_goal(t, spec_path, purpose), task_tools,
                approve=plan_lint(t, doc, protected, log),   # 計画のコード検査（合意018 ④⑤）
                log=log, system=task_system or None,
                max_rounds=limits["max_rounds"], l2_max=limits["l2_max"],
                l2_l1_max=limits["l2_l1_max"],
            )
            t["done"] = bool(result.get("done"))
            if t["done"] and tray:
                # 発行（publish-out）。single-writer（師匠宣言）はここで強制される——
                # 所有者は「そのファイルを最初に産出するタスクのロール」（宣言からの決定論）。
                owner = next(p["role"] for p in tasks if p["file"] == t["file"])
                published, reason = publish(tray, t["file"], t["role"], owner)
                if published:
                    log(("published", t["file"], tray))
                else:
                    t["done"] = False
                    t["last_failure"] = f"発行できない（コードが確認した事実）: {reason}"
                    log(("publish_refused", t["file"], reason))
            if t["done"]:
                clear_failure(t)   # 通ったら前回の失敗は捨てる（持つのは直近1回だけ）
            log(("task_done", t) if t["done"] else ("task_failed", t))
            if not t["done"]:
                return t, [], False
        return None, [], False

    # --- 生命線の LLM 呼び出し（構造化出力） ---
    #
    # やり方（プロンプト）は roles/*.md から来る。コアが供給するのはポジションの契約
    # （スキーマ由来の形の1行）と呼び出し側の環境だけ（合意008）。

    def _process(
        self, model: str, spec: dict, roles: dict, pool: list, log: Callable,
        system: str | None = None, skills: dict | None = None,
    ) -> list:
        # 一覧は人選対象だけ（見せる範囲＝有効な範囲。合意025。人間向け表示と同じ関数）
        roles_s = staffing_lines(roles)
        user = (
            f"SPEC:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
            f"ROLES (your knowledge base):\n{roles_s}\n\n"
            f"AVAILABLE MODELS (default first):\n{', '.join(pool)}"
        )
        data = structured(
            self._l0, model,
            lifeline_system(roles, "pjm", "process", _PROCESS_SCHEMA, system, log, skills),
            user, _PROCESS_SCHEMA,
        )
        return normalize_tasks(data.get("tasks", []), task_roles(roles), log)

    def _decide(
        self, model: str, spec: dict, tasks: list, failure: dict | None,
        failed_checks: list, verdict: dict | None, roles: dict, log: Callable,
        system: str | None = None, skills: dict | None = None,
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
        data = structured(
            self._l0, model,
            lifeline_system(roles, "pjm", "decide", _DECIDE_SCHEMA, system, log, skills),
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


