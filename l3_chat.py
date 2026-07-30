r"""l3_chat.py — L3（大域 Plan / 複雑タスクの完遂）を触る最小 CLI。

L3 = L2 を"単位"として組み合わせ、複雑ゴールを完遂する層。PDCA が完全体で
現れ、P（初回 Plan）と A（再計画）は **HITL 承認スロット**に上がる。この CLI
では承認者＝人間（あなた）。Plan / 再計画のたびに単位一覧を表示し、
    y      = 承認して実行
    d N    = 単位 N を削除（過剰な単位を落として続行）
    n      = 中断
を受ける。D・C（各単位の L2 実行と合否判定）は自律。

上限（MAX_ROUNDS / L2_MAX / L2_L1_MAX）はこの呼び出し側が規定する
（L3 は policy を持たない）。成果物は実ファイルとして cwd に生成される
（file grounding）。ワーキングディレクトリ破壊を避けるため、使い捨ての
ディレクトリで実行すること。

実行中は各層の動きをその場で実況する（層はインデントで入れ子表示）:
    [L3] Plan/失敗分析/全体判定  [L2] Reflect 判定  [L1] 思考  [tool] ツール実行
LLM 呼び出しは開始時に行を出し、完了時に所要秒数を追記する。表示のない沈黙は
ない（沈黙して見える間＝行末が開いている間はローカル LLM が推論中）。
表示は CLI の責務であり、mu の各層は無変更・無関知（プロキシとラッパーで包むだけ）。

使い方:
    .\.venv\Scripts\python.exe l3_chat.py [model]
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
from tools import TOOLS

# Windows コンソール等でも日本語・記号で落ちないよう UTF-8 にそろえる。
for _stream in (sys.stdout, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

DEFAULT_MODEL = "gemma4:12b"  # 参照モデル（他は qwen3.5:9b）
MAX_ROUNDS = 8   # L3 の上限（呼び出し側が規定）
L2_MAX = 6       # 1 単位で L2 を回す上限
L2_L1_MAX = 10   # L2 の 1 周で L1 を回す上限


class _Abort(Exception):
    """人間が承認を拒否して run を止める（HITL の中断）。"""


def _short(text: object, n: int = 120) -> str:
    s = str(text or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def _env_preamble() -> str:
    """各単位の L2 実行へ渡す環境グラウンディング（環境の文脈は呼び出し側の責務）。

    L3 は環境を知らず、この文字列を opaque に L2 へ通すだけ。l2_chat と同じ内容を
    そろえる（弱いモデルが Unix コマンド仮定・パス幻覚に落ちる穴をふさぐ）。
    """
    return (
        "Environment:\n"
        f"- OS: {platform.system()} {platform.release()}\n"
        f"- Working directory: {os.getcwd()}\n"
        "- execute_command runs in PowerShell — use PowerShell/Windows syntax "
        "(e.g. Get-ChildItem, Get-Content), not Unix commands like ls/cat.\n"
        "- Use list_dir to discover files instead of guessing paths."
    )


# --- 実況（表示は CLI の責務。mu の層は無変更・無関知） ------------------------
#
# 沈黙の正体は「L0 の chat（＝ローカル LLM の推論）」と「ツール実行」の2つ。
# 前者は層ごとにラベルを変えた _VerboseL0 を合成点（ToolLoop(l0) / Agent(l0, l1) /
# Orchestrator(l0, l2)）へ差し込んで実況し、後者は _verbose_tools で包んで実況する。

_L3 = "  [L3]"
_L2 = "    [L2]"
_L1 = "      [L1]"
_TOOL = "        [tool]"

# format スキーマの property 集合 → その呼び出しの意味（表示専用。未知形は総称へ）。
_STAGES = {
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
    """表示専用のゆるい JSON 取り出し（壊れていたら None。判定は各層が行う）。"""
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
    """L0 を包み、chat 呼び出しを層ラベル付きで実況するプロキシ。

    開始時に行を開き（沈黙中も何をしているか見える）、完了時に所要秒数を追記する。
    """

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
        # L2 Reflect の合否はほかに表示場所がないのでここで出す
        # （Plan は承認画面が、失敗分析・全体判定は L3 の log が表示する）。
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
    """ツール関数を「実行開始と結果をその場で表示する」ラッパーで包む。

    functools.wraps が __name__・docstring・署名を保つので、L1 の dispatch と
    ollama の関数→スキーマ変換はラップ前と同じに働く。
    """

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
        print(f"{_TOOL}   -> {_short(result)}")
        return result

    return run


def _verbose_tools(tools: list) -> list:
    return [(_verbose_tool(func), usage) for func, usage in tools]


def _show_units(units: list) -> None:
    if not units:
        print("  (単位なし)")
    for i, u in enumerate(units, 1):
        mark = "x" if u.get("done") else " "
        print(f"  {i}. [{mark}] {u.get('file')}")
        print(f"        task: {_short(u.get('task'))}")
        print(f"        基準: {_short(u.get('criterion'))}")
        check = u.get("check") or {}
        if check.get("run"):
            expect = f" → 「{_short(check.get('expect'), 60)}」" if check.get("expect") else ""
            print(f"        検査: {_short(check.get('run'), 80)}{expect}")


def _approve(units: list) -> list:
    """HITL: Plan / 再計画を表示し、承認(y) / 削除(d N) / 中断(n) を受ける。"""
    units = [dict(u) for u in units]  # 破壊しないコピーを編集する
    while True:
        print("── 承認する Plan ──")
        _show_units(units)
        try:
            cmd = input("承認 [y=実行 / d N=単位N削除 / n=中断] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise _Abort()
        if cmd == "y":
            return units
        if cmd == "n":
            raise _Abort()
        if cmd.startswith("d"):
            arg = cmd[1:].strip()
            if arg.isdigit() and 1 <= int(arg) <= len(units):
                removed = units.pop(int(arg) - 1)
                print(f"  -> 削除: {removed.get('file')}")
            else:
                print("  ? 使い方: d <番号>（1〜{}）".format(len(units)))
            continue
        print("  ? y / d N / n のいずれかを入力")


def _log(event: tuple) -> None:
    """自律部（D・C）の進行を表示。plan/replan は _approve が対話表示するので出さない。"""
    kind = event[0]
    if kind == "unit_done":
        print(f"  [x] UNIT DONE  : {event[1].get('file')}")
    elif kind == "unit_failed":
        analysis = event[2]
        print(f"  [!] UNIT FAILED: {event[1].get('file')} -> {_short(analysis.get('reason'))}")
        if analysis.get("suggestion"):
            print(f"      suggestion : {_short(analysis.get('suggestion'))}")
    elif kind == "unit_check_failed":
        print(f"  [!] UNIT CHECK NG: {event[1].get('file')} -> {_short(event[2], 140)}")
    elif kind == "unit_check_skipped":
        print(f"  [?] UNIT CHECK SKIP: {event[1].get('file')} ({_short(event[2], 80)})")
    elif kind == "overall":
        # 機械的照合の結果（全単位 done か）。LLM の推測判定ではない。
        v = event[1]
        print(f"  [=] OVERALL: passed={v.get('passed')} :: {_short(v.get('reason'), 160)}")


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    l0 = OllamaInterface()
    # 層ごとにラベルの違う実況プロキシを合成点へ差し込む（層自体は無変更）。
    # Agent の l0 は Reflect 専用、Orchestrator の l0 は Plan/分析/全体判定専用
    # なので、ラベル＝呼び出し元の層が正確に対応する。
    l1 = ToolLoop(_VerboseL0(l0, _L1))
    l2 = Agent(_VerboseL0(l0, _L2), l1)
    orch = Orchestrator(_VerboseL0(l0, _L3), l2)
    tools = _verbose_tools(TOOLS)

    print(f"L3 chat / model={model}  max_rounds={MAX_ROUNDS}  (複雑ゴールを入力 / /exit で終了)")
    print(f"  cwd={os.getcwd()}  <- 成果物ファイルはここに作られます")
    print("  環境:", platform.system(), platform.release(), "/ execute_command=PowerShell")
    while True:
        try:
            goal = input("goal> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if goal in ("/exit", "/quit"):
            break
        if not goal:
            continue

        try:
            result = orch.run(
                model, goal, tools,
                approve=_approve, log=_log, system=_env_preamble(),
                max_rounds=MAX_ROUNDS, l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
            )
        except _Abort:
            print("— 中断しました")
            continue
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        status = "完遂 ✓" if result["done"] else f"未達 ✗（{result.get('rounds')}周で上限到達）"
        print(f"=== {status} ===")
        for u in result["units"]:
            print(f"  {'[x]' if u.get('done') else '[ ]'} {u.get('file')}")


if __name__ == "__main__":
    main()
