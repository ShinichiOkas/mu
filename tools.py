"""検証用の最小ツール群。

L1 の `(func, usage_text)` ペア形式で提供する。`usage_text` は L1 が
system prompt に注入する「使い方」テキスト。`TOOLS` をそのまま L1 に渡せる:

    from tools import TOOLS
    l1.run(model, messages, TOOLS)

各ツールは `ToolResult`（content: モデル向け散文 / ok: 成否 / facts: 機械可読な
事実）を返す。facts は実体（ディスクの stat・プロセスの exit code）から作る —
判定を「表象」でなく「実体」に寄せるため（合意005）。

注意: write_file / edit_file / execute_command は実ファイル・実シェルに触れる。
検証用途で使うこと。execute_command は PowerShell で実行する。
"""

import shutil
import subprocess
from pathlib import Path

from mu.l1 import ToolResult

# read_file / execute_command の出力上限（LLM 文脈の肥大を防ぐ）。
_MAX_OUTPUT = 4000

# 保護された入力ファイル（絶対パス）。呼び出し側が protect() で登録する。
# 合意006 決定④の解除条件（実走で設計規則が破られ QA/check も検出できない入力破壊を観測）
# の発火により実装。プロンプトの「読み取り専用」規則は確率的にしか効かないため、
# 決定的に守りたい不変条件としてコード側に置く。
# 既知の限界: execute_command 内のシェルリダイレクト等はこの保護を通らない。
_PROTECTED: set = set()


def protect(paths) -> None:
    """指定パスを書き込み禁止（読み取り専用）として登録する。呼び出し側の責務で宣言する。"""
    _PROTECTED.update(str(Path(p).resolve()) for p in paths)


def clear_protection() -> None:
    """保護登録をすべて解除する（テスト・セッション切替用）。"""
    _PROTECTED.clear()


def _protected_result(path: str, action: str) -> ToolResult:
    return ToolResult(
        f"error: {path} is a protected input file (read-only / 保護された入力ファイル)。"
        "上書き・編集は禁止。内容が仕様と食い違う場合は、ファイルを直すのではなく"
        "実物に合わせて作業すること。",
        ok=False,
        facts={"action": action, "path": path, "protected": True},
    )

# PowerShell 実行体。pwsh(7) を優先し、無ければ Windows PowerShell。
_POWERSHELL = shutil.which("pwsh") or shutil.which("powershell") or "powershell"


def read_file(path: str) -> ToolResult:
    """指定パスのファイル内容をテキストで返す。"""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > _MAX_OUTPUT
    shown = text[:_MAX_OUTPUT] + f"\n...(truncated, {len(text)} chars total)" if truncated else text
    return ToolResult(
        shown,
        facts={"action": "read", "path": path, "chars": len(text), "truncated": truncated},
    )


def write_file(path: str, content: str) -> ToolResult:
    """指定パスにテキストを書き込む（新規作成 or 上書き）。"""
    p = Path(path)
    if str(p.resolve()) in _PROTECTED:
        return _protected_result(path, "write")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    size = p.stat().st_size  # 書けた実体の証拠はディスクの stat から取る
    return ToolResult(
        f"wrote {size} bytes to {path}",
        facts={"action": "write", "path": str(p), "bytes": size},
    )


def edit_file(path: str, old: str, new: str) -> ToolResult:
    """ファイル内の文字列 old をすべて new に置換する。"""
    p = Path(path)
    if str(p.resolve()) in _PROTECTED:
        return _protected_result(path, "edit")
    text = p.read_text(encoding="utf-8", errors="replace")
    count = text.count(old)
    if count == 0:
        return ToolResult(
            f"error: 'old' not found in {path}",
            ok=False,
            facts={"action": "edit", "path": str(p), "replacements": 0},
        )
    p.write_text(text.replace(old, new), encoding="utf-8")
    return ToolResult(
        f"replaced {count} occurrence(s) in {path}",
        facts={"action": "edit", "path": str(p), "replacements": count, "bytes": p.stat().st_size},
    )


def list_dir(path: str = ".") -> ToolResult:
    """ディレクトリ内のファイル・フォルダ一覧を返す。"""
    p = Path(path)
    if not p.exists():
        return ToolResult(
            f"error: path not found: {path}", ok=False, facts={"action": "list", "path": path}
        )
    if p.is_file():
        return ToolResult(
            f"file {p.name} ({p.stat().st_size} bytes)",
            facts={"action": "list", "path": path, "bytes": p.stat().st_size},
        )
    lines = []
    for e in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        if e.is_dir():
            lines.append(f"dir  {e.name}/")
        else:
            lines.append(f"file {e.name} ({e.stat().st_size} bytes)")
    return ToolResult(
        "\n".join(lines) if lines else "(empty)",
        facts={"action": "list", "path": path, "entries": len(lines)},
    )


def execute_command(command: str) -> ToolResult:
    """PowerShell でコマンドを実行し、終了コードと標準出力/エラーを返す。"""
    proc = subprocess.run(
        [
            _POWERSHELL, "-NoProfile", "-NonInteractive", "-Command",
            # 出力を UTF-8 に固定してから実行（版差・文字化けを防ぐ）。
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; " + command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    truncated = len(out) > _MAX_OUTPUT
    if truncated:
        out = out[:_MAX_OUTPUT] + f"\n...(truncated, {len(out)} chars total)"
    return ToolResult(
        f"exit={proc.returncode}\n{out}",
        ok=proc.returncode == 0,
        facts={"action": "exec", "exit": proc.returncode, "truncated": truncated},
    )


# --- L1 用の (func, usage_text) ペア ---
READ_FILE = (read_file, "read_file(path): 指定パスのファイル内容を返す。")
WRITE_FILE = (write_file, "write_file(path, content): 指定パスにテキストを書き込む（新規/上書き）。")
EDIT_FILE = (edit_file, "edit_file(path, old, new): ファイル内の old を new に全置換する。")
LIST_DIR = (list_dir, "list_dir(path): ディレクトリ内のファイル/フォルダ一覧を返す（既定は現在ディレクトリ）。")
EXECUTE_COMMAND = (execute_command, "execute_command(command): PowerShell でコマンドを実行し、終了コードと出力を返す。")

TOOLS = [READ_FILE, WRITE_FILE, EDIT_FILE, LIST_DIR, EXECUTE_COMMAND]
