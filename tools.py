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

サイズ無制限（合意010）: 1回の出力は既定窓（`_MAX_OUTPUT`）で守るが、**見えない部分は残さない**。
read_file / list_dir は行単位の窓（offset=読み飛ばす行数・0 始まり / limit=最大行数）を持ち、
切り詰めたら「続きの offset」を散文と facts.next_offset の両方に出す。write_file は
mode="append" で末尾追加でき、1回の生成に収まらない成果物を積み上げられる。execute_command は
長い出力の全文を一時ファイルへ落としてパスを返す（続きは read_file で辿る）。読み出しは全文を
メモリに載せない（行のストリーム読み）。

入力保護（合意006 → 007）: `protect(paths)` で宣言したファイルは write_file / edit_file が
拒否する。守るのは**列挙したファイルの内容不変だけ**で、ディレクトリ不変ではない
（新規ファイルの作成は防がない）。シェルリダイレクト経由の改変もこの層を通らない——
どちらも塞ぐには実行者の正当な能力を削ることになるため、塞がずに
`protection_violations()` で**破れを検出**できるようにしてある（呼び出し側が報告する）。
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from mu.l1 import ToolResult

# 1回の出力の既定窓（LLM 文脈の肥大を防ぐ）。撤廃はしない——**窓を動かせるようにする**（合意010）。
# read_file / list_dir は行単位の窓（offset/limit）を持ち、切り詰めたら「続きの offset」を
# content と facts の両方に出す。execute_command は全文をファイルに落としてパスを案内する。
# どちらも「見えない部分が残らない」ことが要件で、窓の大きさはそのための防衛に過ぎない。
_MAX_OUTPUT = 4000

# 保護された入力ファイル（絶対パス → 登録時の内容ダイジェスト）。呼び出し側が protect() で登録する。
# 合意006 決定④の解除条件（実走で設計規則が破られ QA/check も検出できない入力破壊を観測）
# の発火により実装。プロンプトの「読み取り専用」規則は確率的にしか効かないため、
# 決定的に守りたい不変条件としてコード側に置く。
#
# 意味論（合意007 B2 で明文化）:
#   守るのは「**列挙したファイルの内容が変わらないこと**」だけである。
#   - ディレクトリの不変は保証しない。保護ディレクトリへの**新規ファイル作成は防がない**
#     （H4 のスコープ逸脱はこの意味論の外側。防ぐには実行者の正当な能力を削ることになる）。
#   - write_file / edit_file は拒否できるが、**execute_command 内のシェルリダイレクトは
#     この層を通らない**。塞ぐには任意のコマンド文字列の解析が要り、能力を削る。
#   だから「防ぐ」に加えて「破れたら見える」を用意する: 登録時にダイジェストを控え、
#   protection_violations() で改変・消失を検出できるようにする（塞ぐが観測は殺さない）。
_PROTECTED: dict = {}


def protect(paths) -> None:
    """指定パスを書き込み禁止（読み取り専用）として登録する。呼び出し側の責務で宣言する。

    登録時点の内容ダイジェストを控える（`protection_violations()` の基準になる）。
    """
    for p in paths:
        resolved = Path(p).resolve()
        _PROTECTED[str(resolved)] = _digest(resolved)


def clear_protection() -> None:
    """保護登録をすべて解除する（テスト・セッション切替用）。"""
    _PROTECTED.clear()


def _digest(path: Path) -> str | None:
    """ファイル内容の SHA-256。存在しなければ None。"""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def protection_violations() -> list:
    """保護ファイルのうち、登録時から**内容が変わった / 消えた**ものを返す。

    tools 層を通らない改変（シェルリダイレクト等）は拒否できないが、検出はできる。
    呼び出し側（probe / chat）が走行の最後に報告し、破れを人間に見せるために使う。
    """
    violations = []
    for path, baseline in sorted(_PROTECTED.items()):
        current = _digest(Path(path))
        if current == baseline:
            continue
        violations.append({
            "path": path,
            "status": "missing" if current is None else "modified",
        })
    return violations


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


def _as_int(value, default):
    """モデルが渡した値を int にする。数にならなければ既定値（"200" のような文字列も受ける）。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _take_window(lines, offset: int = 0, limit=None) -> tuple[list, int, int | None]:
    """行のイテレータから窓を切り出す純粋関数。`(shown, total, next_offset)` を返す。

    窓の外の行は保持しない（どんな長さの入力でもメモリに載るのは窓の分だけ）。総数だけは
    最後まで数える——「全体のどこを見ているか」は窓の大きさに依らず要るため。

    窓は「上限に達するまで行を足す」であって、**行を割らない**。割ると offset（行番号）では
    その続きを指せず、辿る手段が消えるため（合意010）。返る量は最大 `_MAX_OUTPUT ＋ 最長行`。
    """
    shown: list = []
    chars = 0
    total = 0
    for i, line in enumerate(lines):
        total += 1
        if i < offset:
            continue
        if limit is not None and len(shown) >= limit:
            continue  # 以降は数えるだけ（total を出すため走査は続ける）
        if shown and chars >= _MAX_OUTPUT:
            continue
        shown.append(line)
        chars += len(line)
    next_offset = offset + len(shown)
    if not shown or next_offset >= total:
        next_offset = None  # 続きが無い（空窓で同じ offset を返して堂々巡りにしない）
    return shown, total, next_offset


def _window_notice(path: str, offset: int, shown: int, total: int, next_offset, unit: str) -> str:
    """切り詰めたときだけ付ける「続きの読み方」。モデルには散文で、検証者には facts で渡す。"""
    if next_offset is None:
        return ""
    tool = "read_file" if unit == "lines" else "list_dir"
    return (
        f"\n...({unit} {offset}-{offset + shown - 1} of {total} shown. "
        f'続き: {tool}("{path}", offset={next_offset}))'
    )


def read_file(path: str, offset: int = 0, limit=None) -> ToolResult:
    """指定パスのファイル内容を行単位の窓で返す（offset=読み飛ばす行数、limit=最大行数）。"""
    offset = max(0, _as_int(offset, 0))
    limit = _as_int(limit, None)
    if limit is not None:
        limit = max(0, limit)
    # 全文を read_text せず1行ずつ流す——窓の外はメモリに載せない（サイズ無制限化の実体）。
    with Path(path).open(encoding="utf-8", errors="replace") as f:
        shown, total, next_offset = _take_window(f, offset, limit)
    text = "".join(shown)
    return ToolResult(
        text + _window_notice(path, offset, len(shown), total, next_offset, "lines"),
        facts={
            "action": "read",
            "path": path,
            "offset": offset,
            "lines": len(shown),
            "total_lines": total,
            "chars": len(text),
            "truncated": next_offset is not None,
            "next_offset": next_offset,
        },
    )


# write_file の mode。弱いモデルの表記ゆれを吸収する（束縛と同じく実行の頑健化）。
_APPEND_MODES = {"append", "a", "add"}
_OVERWRITE_MODES = {"overwrite", "w", "write", "replace", ""}


def write_file(path: str, content: str, mode: str = "overwrite") -> ToolResult:
    """指定パスにテキストを書き込む。mode="append" なら末尾に追加する（既定は上書き）。"""
    p = Path(path)
    if str(p.resolve()) in _PROTECTED:
        return _protected_result(path, "write")  # 追記も内容改変。保護は mode に依らず効く
    normalized = str(mode or "").strip().lower()
    if normalized in _APPEND_MODES:
        append = True
    elif normalized in _OVERWRITE_MODES:
        append = False
    else:
        # 未知の値を黙って上書きに倒すと破壊が起きる。止めて正しい値を案内する。
        return ToolResult(
            f"error: unknown mode {mode!r} for write_file. "
            'use mode="overwrite" (既定・全置き換え) or mode="append" (末尾に追加).',
            ok=False,
            facts={"action": "write", "path": str(p), "mode": normalized, "written": False},
        )
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a" if append else "w", encoding="utf-8") as f:
        f.write(content)
    size = p.stat().st_size  # 書けた実体の証拠はディスクの stat から取る
    added = len(content.encode("utf-8"))
    facts = {"action": "write", "path": str(p), "bytes": size, "mode": "append" if append else "overwrite"}
    if append:
        facts["appended"] = added
        return ToolResult(f"appended {added} bytes to {path} (now {size} bytes)", facts=facts)
    return ToolResult(f"wrote {size} bytes to {path}", facts=facts)


def edit_file(path: str, old: str, new: str) -> ToolResult:
    """ファイル内の文字列 old をすべて new に置換する。"""
    p = Path(path)
    if str(p.resolve()) in _PROTECTED:
        return _protected_result(path, "edit")
    text = p.read_text(encoding="utf-8", errors="replace")
    count = text.count(old)
    if count == 0:
        # 実際に起きる誤用（末尾に足したいのに置換で書こうとする）へ行き先を示す。
        # 追加は write_file 側の責務にした——置換と追加が1関数に同居すると意味論が濁る（合意010）。
        return ToolResult(
            f"error: 'old' not found in {path}. "
            '末尾に足したいなら write_file(path, content, mode="append") を使うこと。',
            ok=False,
            facts={"action": "edit", "path": str(p), "replacements": 0},
        )
    p.write_text(text.replace(old, new), encoding="utf-8")
    return ToolResult(
        f"replaced {count} occurrence(s) in {path}",
        facts={"action": "edit", "path": str(p), "replacements": count, "bytes": p.stat().st_size},
    )


def list_dir(path: str = ".", offset: int = 0, limit=None) -> ToolResult:
    """ディレクトリ内のファイル・フォルダ一覧を返す（read_file と同じ行単位の窓を持つ）。"""
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
    offset = max(0, _as_int(offset, 0))
    limit = _as_int(limit, None)
    if limit is not None:
        limit = max(0, limit)
    entries = (
        f"dir  {e.name}/\n" if e.is_dir() else f"file {e.name} ({e.stat().st_size} bytes)\n"
        for e in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    )
    shown, total, next_offset = _take_window(entries, offset, limit)
    text = "".join(shown).rstrip("\n") if shown else "(empty)"
    return ToolResult(
        text + _window_notice(path, offset, len(shown), total, next_offset, "entries"),
        facts={
            "action": "list",
            "path": path,
            "offset": offset,
            "entries": len(shown),
            "total_entries": total,
            "truncated": next_offset is not None,
            "next_offset": next_offset,
        },
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
    chars = len(out)
    truncated = chars > _MAX_OUTPUT
    output_path = None
    if truncated:
        # 出力はディスクに残らないので、切り詰めるときだけ全文をファイルへ落として辿れるようにする。
        # 続きは既存の read_file(offset=) で読む——新しい機構を足さない（合意010）。
        fd, output_path = tempfile.mkstemp(prefix="mu-exec-", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(out)
        out = (
            out[:_MAX_OUTPUT]
            + f"\n...(truncated, {chars} chars total. "
            + f'全文: read_file("{output_path}", offset=0))'
        )
    return ToolResult(
        f"exit={proc.returncode}\n{out}",
        ok=proc.returncode == 0,
        facts={
            "action": "exec",
            "exit": proc.returncode,
            "chars": chars,
            "truncated": truncated,
            "output_path": output_path,
        },
    )


# --- L1 用の (func, usage_text) ペア ---
READ_FILE = (
    read_file,
    "read_file(path, offset=0, limit=None): ファイル内容を行単位で返す。"
    "offset は読み飛ばす行数（0=先頭）、limit は最大行数。"
    "長いファイルは途中で切れ、末尾に続きの offset が示されるので、"
    "その offset で呼び直せば任意の位置まで読める。",
)
WRITE_FILE = (
    write_file,
    'write_file(path, content, mode="overwrite"): 指定パスにテキストを書き込む。'
    'mode="append" にすると末尾に追加する（長い成果物は分割して積み上げられる）。',
)
EDIT_FILE = (edit_file, "edit_file(path, old, new): ファイル内の old を new に全置換する。")
LIST_DIR = (
    list_dir,
    "list_dir(path, offset=0, limit=None): ディレクトリ内のファイル/フォルダ一覧を返す"
    "（既定は現在ディレクトリ）。件数が多いと切れ、続きの offset が示される。",
)
EXECUTE_COMMAND = (
    execute_command,
    "execute_command(command): PowerShell でコマンドを実行し、終了コードと出力を返す。"
    "出力が長いときは全文をファイルに保存し、そのパスを示す（read_file で続きを読める）。",
)

TOOLS = [READ_FILE, WRITE_FILE, EDIT_FILE, LIST_DIR, EXECUTE_COMMAND]
