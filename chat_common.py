r"""chat_common.py — CLI / probe が共有する実況・環境接地の共通部（層の外）。

mu の層は表示に無変更・無関知（合意003 の観測方針）。ここにあるのは:

- 実況プロキシ `VerboseL0`（L0 を包み、chat 呼び出しを層ラベル付きで表示）
- ツールの実況ラッパー `verbose_tools`（実行開始と結果をその場で表示）
- 走行イベントの表示 `log`（L4/L5 の log= スロットに渡す）
- 環境グラウンディング `env_preamble`（OS/cwd/シェル＋保護入力の宣言。呼び出し側の責務）
- 補助: `utf8_console` / `short` / `Abort` / 層ラベル定数

かつて l3_chat / l5_chat に二重化し、probe 群と l4_chat が l5_chat の
プライベート名を import していた——CLI の一本を事実上のライブラリにしない（023 B1/C1）。
**予算（上限）と既定モデルはここに置かない**——上限は呼び出し側が規定する（各層と同じ思想）。
"""

import functools
import json
import os
import platform
import sys
import time
from pathlib import Path

import tools as tools_mod
from mu.role_kb import L4_ROLES, list_packages, missing_positions, parse_role_doc, staffing_lines

# repo の roles/ を cwd に依らず指す（役割定義書の出所。差し替え可能——合意008）。
ROLES_DIR = str(Path(__file__).resolve().parent / "roles" / "coding")   # 既定＝コーディングパッケージ（合意026）


def roles_paths() -> tuple:
    """ロードする役割パッケージのパス（合意026——切替は L6＝呼び出し側の判断）。

    環境変数 `MU_ROLES_DIR` で指定する（カンマ区切りで複数セットの合成も可）。
    無指定＝コーディングパッケージ。パスは `load_roles(*roles_paths())` にそのまま渡せる。
    どのパッケージがあるかは `roles/<pkg>/manifest.json`（`list_packages`）が名乗る。
    """
    raw = os.environ.get("MU_ROLES_DIR", "")
    paths = tuple(p.strip() for p in raw.split(",") if p.strip())
    return paths or (ROLES_DIR,)


# カタログの root（roles/ 直下＝パッケージたちと director.md の住所。合意028）。
ROLES_ROOT = str(Path(__file__).resolve().parent / "roles")


def roles_auto() -> bool:
    """MU_ROLES_DIR=auto ——パッケージ選択を L5（Director）に委ねる意思表示（合意028。opt-in）。"""
    return os.environ.get("MU_ROLES_DIR", "").strip().lower() == "auto"


def auto_catalog(root: str = ROLES_ROOT) -> tuple:
    """自動選択モードの (カタログ, selector)。

    カタログは `list_packages` の出力から **planned（役割文ゼロの枠）を除外**したもの
    （知識ゼロのチームは選ばせない。カタログは呼び出し側規定なので、これはこの表面の既定）。
    selector はカタログ級定義書 `<root>/director.md`（無ければ None＝知識ゼロで判断。
    不足は L5 側の role_doc_missing で可視化される）。
    """
    packages = [p for p in list_packages(root) if p.get("status") != "planned"]
    doc = Path(root) / "director.md"
    selector = parse_role_doc(doc.read_text(encoding="utf-8")) if doc.is_file() else None
    return packages, selector


def show_catalog(packages: list) -> None:
    """自動選択モードの起動表示: どの範囲から選ばれるか（＝カタログ）を人間にも見せる。"""
    print("[roles] パッケージ自動選択（MU_ROLES_DIR=auto）——カタログ:")
    for p in packages:
        print(f"  - {p.get('name')}（{p.get('status', '?')}）: {short(p.get('description'), 90)}")

# 全層タワー（l4_chat / l5_chat / probe）の層ラベル。浅いタワーの CLI（l3_chat）は
# 自分のインデントを自分で定義する（表示は呼び出し側の持ち物）。
L5 = "  [L5]"
L4 = "   [L4]"
L3 = "     [L3]"
L2 = "       [L2]"
L1 = "        [L1]"
TOOL = "          [tool]"


def utf8_console() -> None:
    """Windows コンソール等でも日本語・記号で落ちないよう UTF-8 にそろえる。"""
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


class Abort(Exception):
    """人間が承認・レビューで終了を選んで run を止める（HITL の中断）。"""


def short(text: object, n: int = 120) -> str:
    s = str(text or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def env_preamble() -> str:
    """タスク実行と check コマンド設計へ渡す環境グラウンディング（呼び出し側の責務）。

    保護された入力があれば**その存在と規範**もここで宣言する（合意018 ④）。宣言が無いと
    計画層は入力の実在を知らず、モック置換の単位を発明する（017 実走の setup_mocks）。
    """
    lines = [
        "Environment:",
        f"- OS: {platform.system()} {platform.release()}",
        f"- Working directory: {os.getcwd()}",
        "- execute_command runs in PowerShell — use PowerShell/Windows syntax "
        "(e.g. Get-ChildItem, Get-Content), not Unix commands like ls/cat.",
        "- Use list_dir to discover files instead of guessing paths.",
    ]
    protected = tools_mod.protected_paths()
    if protected:
        names = ", ".join(os.path.basename(p) for p in protected)
        lines.append(
            f"- PROTECTED INPUT FILES (read-only originals): {names}. "
            "These files ALREADY EXIST and hold the REAL input data. Never overwrite, delete, "
            "recreate or replace them with mock/sample/test data, and never plan a task or "
            "script that does — adapt all work to their actual content."
        )
    return "\n".join(lines)


def show_roles(roles: dict, paths: tuple = ()) -> None:
    """ロード済み役割の表示（合意025——バインディングの透明化）。

    人選対象の一覧は PjM の process プロンプトに載るものと**同じ関数**
    （`staffing_lines`）から出す——人間が見るものと LLM が見るものの一致を構造で保証する。
    渡した役割の集合＝人選の範囲そのもの。4ポジションの定義書不足があれば添える。
    `paths` を渡すと出所も表示する——パッケージなら素性（manifest.json の名前と検証状態）ごと
    （合意026。verified 以外で走っていることが人間に見えるように）。
    """
    for path in paths:
        mf = Path(path) / "manifest.json"
        if mf.is_file():
            m = json.loads(mf.read_text(encoding="utf-8"))
            desc = f" — {m['description']}" if m.get("description") else ""
            print(f"[roles] パッケージ: {m.get('name', Path(path).name)}"
                  f"（{m.get('status', '状態未表明')}）{desc}")
        else:
            print(f"[roles] セット: {path}（マニフェストなし）")
    print("[roles] 人選対象（PjM が見る一覧と同一）:")
    for line in staffing_lines(roles).splitlines():
        print(f"  {line}")
    missing = missing_positions(roles)
    print(f"[roles] ポジション（人選対象外）: {', '.join(L4_ROLES)}"
          + (f" ／ 定義書の不足: {', '.join(missing)}" if missing else ""))


# --- 実況（表示は CLI の責務。mu の層は無変更・無関知） ------------------------
#
# 沈黙の正体は「L0 の chat（＝LLM の推論）」と「ツール実行」の2つ。前者は層ごとに
# ラベルを変えた VerboseL0 を合成点（ToolLoop(l0) / Agent(l0, l1) / …）へ差し込んで
# 実況し、後者は verbose_tools で包んで実況する。

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


class VerboseL0:
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
        # （Plan・分析・判定は各層の log / 承認画面が表示する）。
        fmt = kwargs.get("format")
        if not (isinstance(fmt, dict) and set(fmt.get("properties", {})) == {"passed", "reason", "next"}):
            return
        data = _try_json(getattr(getattr(resp, "message", None), "content", "") or "") or {}
        if "passed" in data:
            print(f"{self._prefix}   -> passed={data.get('passed')} :: {short(data.get('reason'))}")
            if not data.get("passed") and data.get("next"):
                print(f"{self._prefix}   next: {short(data.get('next'))}")

    def __getattr__(self, name: str) -> object:
        return getattr(self._l0, name)


def verbose_tool(func, label: str = TOOL):
    """ツール関数を「実行開始と結果をその場で表示する」ラッパーで包む。

    functools.wraps が __name__・docstring・署名を保つので、L1 の dispatch と
    ollama の関数→スキーマ変換はラップ前と同じに働く。
    """

    @functools.wraps(func)
    def run(*args, **kw):
        shown = ", ".join(
            [short(a, 60) for a in args] + [f"{k}={short(v, 60)}" for k, v in kw.items()]
        )
        print(f"{label} {func.__name__}({shown})", flush=True)
        try:
            result = func(*args, **kw)
        except Exception as e:
            print(f"{label}   -> error: {e}")
            raise  # L1 が捕まえて結果として model へ返す
        content = getattr(result, "content", result)
        print(f"{label}   -> {short(content)}")
        return result

    return run


def verbose_tools(tools: list, label: str = TOOL) -> list:
    return [(verbose_tool(func, label), usage) for func, usage in tools]


# --- 走行イベントの表示（L4 / L5 の log= スロット用） --------------------------

def _show_spec(spec: dict, spec_path: str) -> None:
    print(f"── PdM が定めた仕様（{spec_path} に書き出し済み。直接編集も可）──")
    for d in spec.get("definitions", []):
        print(f"  定義: {d.get('term')} = {short(d.get('definition'), 100)}")
    for c in spec.get("criteria", []):
        print(f"  受入基準: {short(c.get('text'), 100)}")
        if c.get("run"):
            expect = f" → 「{short(c.get('expect'), 60)}」" if c.get("expect") else ""
            print(f"    検査: {short(c.get('run'), 80)}{expect}")
    print(f"  仕様: {short(spec.get('spec'), 200)}")


def _show_process(tasks: list, process_path: str) -> None:
    print(f"── PjM が編んだプロセス（{process_path} に書き出し済み。直接編集も可）──")
    for i, t in enumerate(tasks, 1):
        mark = "x" if t.get("done") else " "
        model = f" @{t['model']}" if t.get("model") else ""
        print(f"  {i}. [{mark}] ({t['role']}{model}) {t['file']}: {short(t['task'], 80)}")


def log(event: tuple) -> None:
    kind = event[0]
    if kind == "package":                 # 合意028: L5 がカタログから自選したパッケージ
        print(f"{L5} パッケージを自選: {event[1]} :: {short(event[2], 140)}")
    elif kind == "spec":
        if len(event) > 2:
            _show_spec(event[1], event[2])
    elif kind == "spec_fallback":
        print(f"{L4} [!] {event[1]}")
    elif kind == "process":
        _show_process(event[1], event[2])
    elif kind == "qa_appended":
        print(f"{L4} [+] QA タスクをコードが補完: {event[1]}")
    elif kind == "infeasible":            # 合意007 C1: 目的が充足不能と申告された
        print(f"{L4} [!] 目的が充足不能と申告された（仕様は作らず人間へ）:")
        for c in event[1] or ["(申告なし)"]:
            print(f"{L4}     - {short(c, 160)}")
    elif kind == "inputs":                # 合意007 C2: PdM に前置した入力の実物
        print(f"{L4} 入力の実物を PdM に接地:")
        for line in str(event[1]).splitlines()[:12]:
            print(f"{L4}   {short(line, 120)}")
    elif kind == "role_doc_missing":      # 合意008: 役割は認識しているが知識が無い状態
        print(f"{L4} [!] 役割定義が無い（{event[1]} / {event[2]}）— 指示なしで実行する")
    elif kind == "permission_denied":     # 合意007 B1: 役割の権限で書き込みを拒否した
        print(f"{L4} [!] 権限で拒否: ({event[1]}) {event[2]} -> {event[3]}")
    elif kind == "tool_withheld":
        print(f"{L4} [-] ツール非配布: ({event[1]}) {event[2]}")
    elif kind == "role_fallback":
        print(f"{L4} [?] 未知の役割 {event[1]} を implementer に置換")
    elif kind == "task_done":
        print(f"{L4} [x] TASK DONE  : ({event[1]['role']}) {event[1]['file']}")
    elif kind == "task_failed":
        print(f"{L4} [!] TASK FAILED: ({event[1]['role']}) {event[1]['file']}")
    elif kind == "checks":
        for c in event[1]:
            # 未検査（run が無い＝誰も機械的に見ていない）を「skip」に紛れさせない。
            # 隠れた合格を作らないための可視化（合意015 B）。
            if c.get("kind") == "unverified":
                mark = "未検査"
            else:
                mark = "ok" if c.get("ok") else ("skip" if c.get("ok") is None else "NG")
            print(f"{L4} 検査[{mark}] {short(c.get('text'), 80)} :: {short(c.get('detail'), 100)}")
        unverified = [c for c in event[1] if c.get("kind") == "unverified"]
        if unverified:
            print(f"{L4} [!] 機械的に検査されていない受入基準が {len(unverified)} 件ある"
                  "（judge / QA の判断のみ）")
    elif kind == "verdict":
        v = event[1]
        # 017: どの項目で落ちたかを見せる。総合値だけだと「何が足りないか」が人間に届かない。
        for item in v.get("items", []):
            mark = {"pass": "PASS", "fail": "FAIL"}.get(item["verdict"], "不明")
            print(f"{L4}   [{mark}] #{item['n']} {short(item['text'], 60)} :: "
                  f"{short(item.get('evidence'), 80)}")
        print(f"{L4} QA 判定（集約はコード）: {v.get('achieved')} :: {short(v.get('reason'), 160)}")
        if v.get("gap"):
            print(f"{L4}   gap: {short(v.get('gap'), 160)}")
    elif kind == "pjm":
        d = event[1]
        inv = f" invalidate={d.get('invalidate')}" if d.get("invalidate") else ""
        print(f"{L4} PjM 判断: {d.get('action')}{inv} :: {short(d.get('reason'), 140)}")
    elif kind == "respec":
        print(f"{L4} 仕様を改訂して再実行: {short(event[1], 160)}")
    elif kind in ("plan", "replan"):
        print(f"{L3} Plan{'（再計画）' if kind == 'replan' else ''}を自律承認:")
        for i, u in enumerate(event[1], 1):
            mark = "x" if u.get("done") else " "
            print(f"{L3}   {i}. [{mark}] {u.get('file')}: {short(u.get('task'), 80)}")
    elif kind == "unit_done":
        print(f"{L3} [x] UNIT DONE  : {event[1].get('file')}")
    elif kind == "unit_failed":
        analysis = event[2]
        print(f"{L3} [!] UNIT FAILED: {event[1].get('file')} -> {short(analysis.get('reason'))}")
    elif kind == "unit_check_failed":
        print(f"{L3} [!] UNIT CHECK NG: {event[1].get('file')} -> {short(event[2], 140)}")
    elif kind == "unit_check_skipped":
        print(f"{L3} [?] UNIT CHECK SKIP: {event[1].get('file')} ({short(event[2], 80)})")
    elif kind == "overall":
        v = event[1]
        print(f"{L3} [=] OVERALL: passed={v.get('passed')} :: {short(v.get('reason'), 160)}")
