"""検証用の最小ツール群。

L1 の `(func, usage_text)` ペア形式で提供する。`usage_text` は L1 が
system prompt に注入する「使い方」テキスト。`TOOLS` をそのまま L1 に渡せる:

    from tools import TOOLS
    l1.run(model, messages, TOOLS)

注意: write_file / edit_file / execute_command は実ファイル・実シェルに触れる。
検証用途で使うこと。execute_command は PowerShell で実行する。
"""

import shutil
import subprocess
from pathlib import Path

# read_file / execute_command の出力上限（LLM 文脈の肥大を防ぐ）。
_MAX_OUTPUT = 4000

# PowerShell 実行体。pwsh(7) を優先し、無ければ Windows PowerShell。
_POWERSHELL = shutil.which("pwsh") or shutil.which("powershell") or "powershell"


def read_file(path: str) -> str:
    """指定パスのファイル内容をテキストで返す。"""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    if len(text) > _MAX_OUTPUT:
        return text[:_MAX_OUTPUT] + f"\n...(truncated, {len(text)} chars total)"
    return text


def write_file(path: str, content: str) -> str:
    """指定パスにテキストを書き込む（新規作成 or 上書き）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} chars to {path}"


def edit_file(path: str, old: str, new: str) -> str:
    """ファイル内の文字列 old をすべて new に置換する。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    count = text.count(old)
    if count == 0:
        return f"error: 'old' not found in {path}"
    p.write_text(text.replace(old, new), encoding="utf-8")
    return f"replaced {count} occurrence(s) in {path}"


def list_dir(path: str = ".") -> str:
    """ディレクトリ内のファイル・フォルダ一覧を返す。"""
    p = Path(path)
    if not p.exists():
        return f"error: path not found: {path}"
    if p.is_file():
        return f"file {p.name} ({p.stat().st_size} bytes)"
    lines = []
    for e in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        if e.is_dir():
            lines.append(f"dir  {e.name}/")
        else:
            lines.append(f"file {e.name} ({e.stat().st_size} bytes)")
    return "\n".join(lines) if lines else "(empty)"


def execute_command(command: str) -> str:
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
    if len(out) > _MAX_OUTPUT:
        out = out[:_MAX_OUTPUT] + f"\n...(truncated, {len(out)} chars total)"
    return f"exit={proc.returncode}\n{out}"


# --- L1 用の (func, usage_text) ペア ---
READ_FILE = (read_file, "read_file(path): 指定パスのファイル内容を返す。")
WRITE_FILE = (write_file, "write_file(path, content): 指定パスにテキストを書き込む（新規/上書き）。")
EDIT_FILE = (edit_file, "edit_file(path, old, new): ファイル内の old を new に全置換する。")
LIST_DIR = (list_dir, "list_dir(path): ディレクトリ内のファイル/フォルダ一覧を返す（既定は現在ディレクトリ）。")
EXECUTE_COMMAND = (execute_command, "execute_command(command): PowerShell でコマンドを実行し、終了コードと出力を返す。")

TOOLS = [READ_FILE, WRITE_FILE, EDIT_FILE, LIST_DIR, EXECUTE_COMMAND]
