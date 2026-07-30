r"""l4_chat.py — L4（目的の層 / Director）を触る最小 CLI。

L4 = 目的（なぜ作るか）を受け取り、操作的定義＋完了条件＋仕様に変換して
L3 に完遂させ、成果を**目的**に照らして判定する層。

HITL の位置が L3 と変わる（合意005「承認の位置が一段低すぎた」）:
  - L3 の Plan / 再計画の承認 = **L4 が自律**（人間には流れが実況されるだけ）
  - 人間が判断するのは**目的の達成**だけ。定義は事前確認せず、決めて明示し
    動かして見せてから直す（SPEC.md を直接編集してもよい）
最終判定のプロンプトで
    y      = 目的達成として受理
    f XXX  = フィードバック XXX で仕様を改訂して再実行
    n      = 終了（未達のまま引き取る）
を受ける。L4 の判定が uncertain（判定できない）のときも、黙って完遂にせず
ここに上がってくる — それが偽・完遂の再発防止線。

上限（L4_MAX / L3_MAX / L2_MAX / L2_L1_MAX）はこの呼び出し側が規定する。
成果物ファイルと SPEC.md は cwd に生成される（file grounding）。使い捨ての
ディレクトリで実行すること。

使い方:
    .\.venv\Scripts\python.exe l4_chat.py [model]
既定モデルは gemma4:12b（参照モデル。もう一つは qwen3.5:9b）。
"""

import functools
import json
import os
import platform
import sys
import time

from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from mu.l2 import Agent
from mu.l3 import Orchestrator
from mu.l4 import Director
from tools import TOOLS

# Windows コンソール等でも日本語・記号で落ちないよう UTF-8 にそろえる。
for _stream in (sys.stdout, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

DEFAULT_MODEL = "gemma4:12b"  # 参照モデル（他は qwen3.5:9b）
L4_MAX = 3       # L4 の上限（仕様改訂→再実行の回数）
L3_MAX = 8       # 1 仕様で L3 を回す上限
L2_MAX = 6       # 1 単位で L2 を回す上限
L2_L1_MAX = 10   # L2 の 1 周で L1 を回す上限


class _Abort(Exception):
    """人間がレビューで終了を選んで run を止める（HITL の中断）。"""


def _short(text: object, n: int = 120) -> str:
    s = str(text or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def _env_preamble() -> str:
    """L2 実行へ渡す環境グラウンディング（環境の文脈は呼び出し側の責務）。"""
    return (
        "Environment:\n"
        f"- OS: {platform.system()} {platform.release()}\n"
        f"- Working directory: {os.getcwd()}\n"
        "- execute_command runs in PowerShell — use PowerShell/Windows syntax "
        "(e.g. Get-ChildItem, Get-Content), not Unix commands like ls/cat.\n"
        "- Use list_dir to discover files instead of guessing paths."
    )


# --- 実況（表示は CLI の責務。mu の層は無変更・無関知） ------------------------

_L4 = "  [L4]"
_L3 = "    [L3]"
_L2 = "      [L2]"
_L1 = "        [L1]"
_TOOL = "          [tool]"

# format スキーマの property 集合 → その呼び出しの意味（表示専用。未知形は総称へ）。
_STAGES = {
    frozenset({"definitions", "criteria", "spec"}): "仕様を策定中（目的→定義/完了条件/仕様）",
    frozenset({"achieved", "reason", "gap"}): "目的達成を判定中",
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
    print(f"── L4 が定めた仕様（{spec_path} に書き出し済み。直接編集も可）──")
    for d in spec.get("definitions", []):
        print(f"  定義: {d.get('term')} = {_short(d.get('definition'), 100)}")
    for c in spec.get("criteria", []):
        print(f"  完了条件: {_short(c, 100)}")
    print(f"  仕様: {_short(spec.get('spec'), 200)}")


def _log(event: tuple) -> None:
    """自律部の進行を表示。L3 の Plan 承認は L4 が自律なので、Plan も表示だけする。"""
    kind = event[0]
    if kind == "spec":
        _show_spec(event[1], event[2])
    elif kind == "spec_fallback":
        print(f"{_L4} [!] {event[1]}")
    elif kind == "assess":
        a = event[1]
        print(f"{_L4} 目的判定: {a.get('achieved')} :: {_short(a.get('reason'), 160)}")
        if a.get("gap"):
            print(f"{_L4}   gap: {_short(a.get('gap'), 160)}")
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
    elif kind == "overall":
        v = event[1]
        print(f"{_L3} [=] OVERALL: passed={v.get('passed')} :: {_short(v.get('reason'), 160)}")


def _review(report: dict) -> dict:
    """HITL: 目的の達成を人間が判断する（再帰の底）。"""
    a = report.get("assessment", {})
    units = report.get("result", {}).get("units", [])
    print("── 目的レビュー ──")
    print(f"  目的: {_short(report.get('purpose'), 160)}")
    print(f"  L4 の判定: {a.get('achieved')} :: {_short(a.get('reason'), 200)}")
    if a.get("gap"):
        print(f"  gap: {_short(a.get('gap'), 200)}")
    print("  成果物:")
    for u in units:
        print(f"    {'[x]' if u.get('done') else '[ ]'} {u.get('file')}")
    print(f"  仕様書: {report.get('spec_path')}（定義・完了条件はここ）")
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
    l0 = OllamaInterface()
    # 層ごとにラベルの違う実況プロキシを合成点へ差し込む（層自体は無変更）。
    l1 = ToolLoop(_VerboseL0(l0, _L1))
    l2 = Agent(_VerboseL0(l0, _L2), l1)
    l3 = Orchestrator(_VerboseL0(l0, _L3), l2)
    director = Director(_VerboseL0(l0, _L4), l3)
    tools = _verbose_tools(TOOLS)

    print(f"L4 chat / model={model}  l4_max={L4_MAX}  (目的を入力 / /exit で終了)")
    print(f"  cwd={os.getcwd()}  <- 成果物と SPEC.md はここに作られます")
    print("  環境:", platform.system(), platform.release(), "/ execute_command=PowerShell")
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
                review=_review, log=_log, system=_env_preamble(),
                max_rounds=L4_MAX, l3_max=L3_MAX, l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
            )
        except _Abort:
            print("— 終了（未達のまま引き取り）")
            continue
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        if result["achieved"]:
            status = "目的達成（人間が受理）✓"
        elif result["escalated"]:
            a = result.get("assessment", {})
            status = f"未達（{a.get('achieved')}: {_short(a.get('reason'), 120)}）"
        else:
            status = "未達"
        print(f"=== {status} ===")
        print(f"  仕様書: {result.get('spec_path')} / L4 {result.get('rounds')}周")


if __name__ == "__main__":
    main()
