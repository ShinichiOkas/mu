r"""l5_chat.py — L5（目的の層 / PdM）を触る最小 CLI。目的を1行入れると全層が動く。

L5 = 目的（なぜ作るか）を受け取り、
  PdM がまず**充足可能性**を申告し（制約が同時に満たせなければ仕様を作らず人間へ上げる）、
  可能なら**作業ディレクトリの入力の実物**に接地して操作的定義＋受入基準＋仕様（SPEC.md）を定め、
  PjM が役割注釈付きプロセス（PROCESS.md）を編んで人選し、
  1タスクずつ役割を着せた L3 に完遂させ、
  末尾の QA タスク（独立文脈。SPEC・実物・**目的の原文**を見る）が書く verdict.md を
  機械的に読んで判定する層。

役割定義書はリポジトリの roles/ から読む（`mu.role_kb`。**出所は差し替え可能**で、
同じ形の dict を返せば L4 は無変更）。定義書は PjM のナレッジベースであると同時に
**役割の権限の宣言**（frontmatter の tools / write_scope）でもあり、権限はコードが適用する
——PjM が出せるのは役割名だけなので、権限は LLM 側から書き換えられない。
**5役割（pdm / pjm / architect / implementer / qa）すべてのやり方が定義書にあり**、
コード内に生命線プロンプトは無い。定義書が欠けた役割は「知識が無い状態」で動く
（その事実は `role_doc_missing` として実況に出る）。
失敗や verdict 不合格は PjM が部分再実行（rerun/replan/respec）を判断し、
判断できないときは人間に上がる。最終判定のプロンプトで
    y      = 目的達成として受理
    f XXX  = フィードバック XXX で仕様を改訂して再実行
    n      = 終了（未達のまま引き取る）
を受ける。

上限（L5_MAX / L4_MAX / L3_MAX / L2_MAX / L2_L1_MAX）はこの呼び出し側が規定する（予算の封筒）。
成果物・SPEC.md・PROCESS.md・verdict.md は cwd に生成される（file grounding）。
使い捨てのディレクトリで実行すること。

使い方:
    .\.venv\Scripts\python.exe l5_chat.py [model] [追加モデル...]
追加モデルは PjM の人選プール（例: QA を別ファミリーに出す qwen3.5:9b）。
既定モデルは gemma4:12b。開発回転は gemma4:31b-cloud を推奨（役割別3構成）。
"""

import functools
import json
import os
import platform
import sys
import time
from pathlib import Path

from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from mu.l2 import Agent
from mu.l3 import Orchestrator
from mu.l4 import Manager
from mu.l5 import Director
from mu.role_kb import load_roles
import tools as tools_mod
from tools import TOOLS

# Windows コンソール等でも日本語・記号で落ちないよう UTF-8 にそろえる。
for _stream in (sys.stdout, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

DEFAULT_MODEL = "gemma4:12b"
ROLES_DIR = str(Path(__file__).resolve().parent / "roles")  # cwd に依らず repo の roles/ を読む
L5_MAX = 2       # L5 の上限（respec サイクル＝仕様を直して回し直す回数）
L4_MAX = 3       # L4 の上限（PjM 判断サイクル＝rerun/replan の回数）
L3_MAX = 8       # 1 タスクで L3 を回す上限
L2_MAX = 6       # 1 単位で L2 を回す上限
L2_L1_MAX = 10   # L2 の 1 周で L1 を回す上限


class _Abort(Exception):
    """人間がレビューで終了を選んで run を止める（HITL の中断）。"""


def _short(text: object, n: int = 120) -> str:
    s = str(text or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def _env_preamble() -> str:
    """タスク実行と check コマンド設計へ渡す環境グラウンディング（呼び出し側の責務）。"""
    return (
        "Environment:\n"
        f"- OS: {platform.system()} {platform.release()}\n"
        f"- Working directory: {os.getcwd()}\n"
        "- execute_command runs in PowerShell — use PowerShell/Windows syntax "
        "(e.g. Get-ChildItem, Get-Content), not Unix commands like ls/cat.\n"
        "- Use list_dir to discover files instead of guessing paths."
    )


# --- 実況（表示は CLI の責務。mu の層は無変更・無関知） ------------------------

_L5 = "  [L5]"
_L4 = "   [L4]"
_L3 = "     [L3]"
_L2 = "       [L2]"
_L1 = "        [L1]"
_TOOL = "          [tool]"

# format スキーマの property 集合 → その呼び出しの意味（表示専用。未知形は総称へ）。
_STAGES = {
    frozenset({"definitions", "criteria", "spec"}): "仕様を策定中（PdM: 定義/受入基準/仕様）",
    frozenset({"tasks"}): "プロセスを編成中（PjM: 役割・人選・順序）",
    frozenset({"action", "invalidate", "reason"}): "進め方を判断中（PjM: 部分再実行）",
    frozenset({"units"}): "Plan/再計画を作成中",
    frozenset({"reason", "suggestion"}): "失敗を分析中",
    frozenset({"passed", "reason", "next"}): "Reflect（合否）判定中",
}


def _stage(kwargs: dict) -> str:
    if kwargs.get("tools"):
        return "思考中（次の行動を決定）"
    fmt = kwargs.get("format")
    if isinstance(fmt, dict):
        return _STAGES.get(frozenset(fmt.get("properties", {})), "構造化出力を生成中")
    return "応答を生成中"


def _try_json(text: str) -> dict | None:
    start, end = (text or "").find("{"), (text or "").rfind("}")
    if 0 <= start < end:
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict):
            return data
    return None


class _VerboseL0:
    """L0 を包み、chat 呼び出しを層ラベル付きで実況するプロキシ。"""

    def __init__(self, l0: object, prefix: str) -> None:
        self._l0 = l0
        self._prefix = prefix

    def chat(self, model: str, messages: list, **kwargs: object) -> object:
        print(f"{self._prefix} {_stage(kwargs)}…", end="", flush=True)
        t0 = time.monotonic()
        try:
            resp = self._l0.chat(model, messages, **kwargs)  # type: ignore[attr-defined]
        except BaseException:
            print()  # 失敗しても開いた行を閉じる
            raise
        tokens = getattr(resp, "eval_count", None)
        print(f" ({time.monotonic() - t0:.1f}s{f', {tokens} tok' if tokens else ''})")
        self._show_verdict(resp, kwargs)
        return resp

    def _show_verdict(self, resp: object, kwargs: dict) -> None:
        # L2 Reflect の合否はほかに表示場所がないのでここで出す。
        fmt = kwargs.get("format")
        if not (isinstance(fmt, dict) and set(fmt.get("properties", {})) == {"passed", "reason", "next"}):
            return
        data = _try_json(getattr(getattr(resp, "message", None), "content", "") or "") or {}
        if "passed" in data:
            print(f"{self._prefix}   -> passed={data.get('passed')} :: {_short(data.get('reason'))}")
            if not data.get("passed") and data.get("next"):
                print(f"{self._prefix}   next: {_short(data.get('next'))}")

    def __getattr__(self, name: str) -> object:
        return getattr(self._l0, name)


def _verbose_tool(func):
    """ツール関数を「実行開始と結果をその場で表示する」ラッパーで包む。"""

    @functools.wraps(func)
    def run(*args, **kw):
        shown = ", ".join(
            [_short(a, 60) for a in args] + [f"{k}={_short(v, 60)}" for k, v in kw.items()]
        )
        print(f"{_TOOL} {func.__name__}({shown})", flush=True)
        try:
            result = func(*args, **kw)
        except Exception as e:
            print(f"{_TOOL}   -> error: {e}")
            raise  # L1 が捕まえて結果として model へ返す
        content = getattr(result, "content", result)
        print(f"{_TOOL}   -> {_short(content)}")
        return result

    return run


def _verbose_tools(tools: list) -> list:
    return [(_verbose_tool(func), usage) for func, usage in tools]


def _show_spec(spec: dict, spec_path: str) -> None:
    print(f"── PdM が定めた仕様（{spec_path} に書き出し済み。直接編集も可）──")
    for d in spec.get("definitions", []):
        print(f"  定義: {d.get('term')} = {_short(d.get('definition'), 100)}")
    for c in spec.get("criteria", []):
        print(f"  受入基準: {_short(c.get('text'), 100)}")
        if c.get("run"):
            expect = f" → 「{_short(c.get('expect'), 60)}」" if c.get("expect") else ""
            print(f"    検査: {_short(c.get('run'), 80)}{expect}")
    print(f"  仕様: {_short(spec.get('spec'), 200)}")


def _show_process(tasks: list, process_path: str) -> None:
    print(f"── PjM が編んだプロセス（{process_path} に書き出し済み。直接編集も可）──")
    for i, t in enumerate(tasks, 1):
        mark = "x" if t.get("done") else " "
        model = f" @{t['model']}" if t.get("model") else ""
        print(f"  {i}. [{mark}] ({t['role']}{model}) {t['file']}: {_short(t['task'], 80)}")


def _log(event: tuple) -> None:
    kind = event[0]
    if kind == "spec":
        _show_spec(event[1], event[2]) if len(event) > 2 else None
    elif kind == "spec_fallback":
        print(f"{_L4} [!] {event[1]}")
    elif kind == "process":
        _show_process(event[1], event[2])
    elif kind == "qa_appended":
        print(f"{_L4} [+] QA タスクをコードが補完: {event[1]}")
    elif kind == "infeasible":            # 合意007 C1: 目的が充足不能と申告された
        print(f"{_L4} [!] 目的が充足不能と申告された（仕様は作らず人間へ）:")
        for c in event[1] or ["(申告なし)"]:
            print(f"{_L4}     - {_short(c, 160)}")
    elif kind == "inputs":                # 合意007 C2: PdM に前置した入力の実物
        print(f"{_L4} 入力の実物を PdM に接地:")
        for line in str(event[1]).splitlines()[:12]:
            print(f"{_L4}   {_short(line, 120)}")
    elif kind == "role_doc_missing":      # 合意008: 役割は認識しているが知識が無い状態
        print(f"{_L4} [!] 役割定義が無い（{event[1]} / {event[2]}）— 指示なしで実行する")
    elif kind == "permission_denied":     # 合意007 B1: 役割の権限で書き込みを拒否した
        print(f"{_L4} [!] 権限で拒否: ({event[1]}) {event[2]} -> {event[3]}")
    elif kind == "tool_withheld":
        print(f"{_L4} [-] ツール非配布: ({event[1]}) {event[2]}")
    elif kind == "role_fallback":
        print(f"{_L4} [?] 未知の役割 {event[1]} を implementer に置換")
    elif kind == "task_done":
        print(f"{_L4} [x] TASK DONE  : ({event[1]['role']}) {event[1]['file']}")
    elif kind == "task_failed":
        print(f"{_L4} [!] TASK FAILED: ({event[1]['role']}) {event[1]['file']}")
    elif kind == "checks":
        for c in event[1]:
            # 未検査（run が無い＝誰も機械的に見ていない）を「skip」に紛れさせない。
            # 隠れた合格を作らないための可視化（合意015 B）。
            if c.get("kind") == "unverified":
                mark = "未検査"
            else:
                mark = "ok" if c.get("ok") else ("skip" if c.get("ok") is None else "NG")
            print(f"{_L4} 検査[{mark}] {_short(c.get('text'), 80)} :: {_short(c.get('detail'), 100)}")
        unverified = [c for c in event[1] if c.get("kind") == "unverified"]
        if unverified:
            print(f"{_L4} [!] 機械的に検査されていない受入基準が {len(unverified)} 件ある"
                  "（judge / QA の判断のみ）")
    elif kind == "verdict":
        v = event[1]
        # 017: どの項目で落ちたかを見せる。総合値だけだと「何が足りないか」が人間に届かない。
        for item in v.get("items", []):
            mark = {"pass": "PASS", "fail": "FAIL"}.get(item["verdict"], "不明")
            print(f"{_L4}   [{mark}] #{item['n']} {_short(item['text'], 60)} :: "
                  f"{_short(item.get('evidence'), 80)}")
        print(f"{_L4} QA 判定（集約はコード）: {v.get('achieved')} :: {_short(v.get('reason'), 160)}")
        if v.get("gap"):
            print(f"{_L4}   gap: {_short(v.get('gap'), 160)}")
    elif kind == "pjm":
        d = event[1]
        inv = f" invalidate={d.get('invalidate')}" if d.get("invalidate") else ""
        print(f"{_L4} PjM 判断: {d.get('action')}{inv} :: {_short(d.get('reason'), 140)}")
    elif kind == "respec":
        print(f"{_L4} 仕様を改訂して再実行: {_short(event[1], 160)}")
    elif kind in ("plan", "replan"):
        print(f"{_L3} Plan{'（再計画）' if kind == 'replan' else ''}を自律承認:")
        for i, u in enumerate(event[1], 1):
            mark = "x" if u.get("done") else " "
            print(f"{_L3}   {i}. [{mark}] {u.get('file')}: {_short(u.get('task'), 80)}")
    elif kind == "unit_done":
        print(f"{_L3} [x] UNIT DONE  : {event[1].get('file')}")
    elif kind == "unit_failed":
        analysis = event[2]
        print(f"{_L3} [!] UNIT FAILED: {event[1].get('file')} -> {_short(analysis.get('reason'))}")
    elif kind == "unit_check_failed":
        print(f"{_L3} [!] UNIT CHECK NG: {event[1].get('file')} -> {_short(event[2], 140)}")
    elif kind == "unit_check_skipped":
        print(f"{_L3} [?] UNIT CHECK SKIP: {event[1].get('file')} ({_short(event[2], 80)})")
    elif kind == "overall":
        v = event[1]
        print(f"{_L3} [=] OVERALL: passed={v.get('passed')} :: {_short(v.get('reason'), 160)}")


def _review(report: dict) -> dict:
    """HITL: 目的の達成を人間が判断する（再帰の底）。"""
    a = report.get("assessment", {})
    print("── 目的レビュー ──")
    print(f"  目的: {_short(report.get('purpose'), 160)}")
    print(f"  ラウンド: {'完全 ok' if report.get('ok') else '未達あり'}")
    print(f"  QA 判定: {a.get('achieved')} :: {_short(a.get('reason'), 200)}")
    if a.get("gap"):
        print(f"  gap: {_short(a.get('gap'), 200)}")
    print("  プロセス:")
    for t in report.get("tasks", []):
        model = f" @{t['model']}" if t.get("model") else ""
        print(f"    {'[x]' if t.get('done') else '[ ]'} ({t['role']}{model}) {t['file']}")
    print(f"  仕様書: {report.get('spec_path')} / 体制表: {report.get('process_path')}")
    while True:
        try:
            cmd = input("目的は達成？ [y=受理 / f <指示>=改訂して再実行 / n=終了] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise _Abort()
        if cmd == "y":
            return {"accept": True}
        if cmd == "n":
            raise _Abort()
        if cmd.startswith("f"):
            feedback = cmd[1:].strip()
            if feedback:
                return {"accept": False, "feedback": feedback}
            print("  ? 使い方: f <指示>（例: f 閾値は3%にして）")
            continue
        print("  ? y / f <指示> / n のいずれかを入力")


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    pool = [model, *sys.argv[2:]]
    roles = load_roles(ROLES_DIR)
    l0 = OllamaInterface()
    l1 = ToolLoop(_VerboseL0(l0, _L1))
    l2 = Agent(_VerboseL0(l0, _L2), l1)
    l3 = Orchestrator(_VerboseL0(l0, _L3), l2)
    l4 = Manager(_VerboseL0(l0, _L4), l3)
    director = Director(_VerboseL0(l0, _L5), l4)
    tools = _verbose_tools(TOOLS)

    print(f"L5 chat / model={model}  pool={pool}  roles={sorted(roles)}  l5_max={L5_MAX} l4_max={L4_MAX}")
    print(f"  cwd={os.getcwd()}  <- 成果物・SPEC.md・PROCESS.md・verdict.md はここに作られます")
    print("  環境:", platform.system(), platform.release(), "/ execute_command=PowerShell")
    print("  (目的を入力 / /exit で終了)")
    while True:
        try:
            purpose = input("purpose> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if purpose in ("/exit", "/quit"):
            break
        if not purpose:
            continue

        try:
            result = director.run(
                model, purpose, tools,
                roles=roles, models=pool,
                review=_review, log=_log, system=_env_preamble(),
                guard=tools_mod.protection_violations,  # 守られるべき入力の破れで即停止（合意016）
                max_rounds=L5_MAX, l4_max=L4_MAX, l3_max=L3_MAX,
                l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
            )
        except _Abort:
            print("— 終了（未達のまま引き取り）")
            continue
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        if result["achieved"]:
            status = "目的達成（人間が受理）✓"
        else:
            a = result.get("assessment", {})
            status = f"未達（{a.get('achieved')}: {_short(a.get('reason'), 120)}）"
        print(f"=== {status} ===")
        print(f"  体制表: {result.get('process_path')} / L4 {result.get('rounds')}周")


if __name__ == "__main__":
    main()
