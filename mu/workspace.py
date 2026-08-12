"""作業空間（tray）— 層の外にある facility（合意030）。

師匠の宣言:「入出力ファイルは共有空間に置く、作業ファイルは個別ディレクトリに置く。
入力ファイルは複数ロールで共有してもよいが、出力ファイルは複数ロールで共有してはいけない。
つまり書き込みができるロールは1に固定」。

機構は copy-in / publish-out:

  - タスク開始時、needs（＋SPEC）を tray（`<work>/<role>/task-N/`）へ**写す**（スナップショット）
  - タスクのツールは tray に**閉じる**（相対パスは tray 起点に解決。tray 外はコードが拒否）
  - 完了時、コードが宣言された出力を共有空間へ**発行**する。失敗したタスクは発行しない
    （半端な成果物が共有空間に出ない）。**single-writer はここで強制する**——
    別ロールの発行は拒否し、タスクは可視に失敗して PjM の decide に乗る

未宣言の依存は「静かなレース」ではなく「そのタスクの可視な失敗」（tray に無いから読めない）に
なる——**依存グラフは構成的に真**。これが並列化（次スプリント）の安全の根拠。
`execute_command` の絶対パス逃げは塞げない破れとして残る（入力保護と同型: 防止ではなく検出。
guard は共有空間の原本を見張り、tray の写しへの変更は原本に届かない）。

tray は role 配下にタスク単位で切る（`<work>/<role>/task-N/`）。role 共有の scratch は
タスク間の隠れ結合（宣言外の依存）を許してしまう——役割ごとの机の中のタスクごとのトレー。
tray はタスクの再実行で再利用されるが、**宣言された出力だけは実行前に消す**
（前回試行の残骸を発行させない。scratch は観測のために残す）。

例外が1つ: `read_file` は**システム一時ディレクトリ直下のファイル**だけ読んでよい。
`execute_command` の長い出力は全文が一時ファイル（temp 直下）に保存され read_file で
辿る契約（合意010「見えない部分を残さない」）であり、閉じると観測が死ぬ。
直下限定なのは、temp 配下の他ディレクトリ（別プロセスの作業領域等）まで開けないため。
"""

from __future__ import annotations

import shutil
import tempfile
from functools import wraps
from pathlib import Path
from typing import Callable, Sequence

from .l1 import Tool, ToolResult

_PATH_TOOLS = ("read_file", "write_file", "edit_file", "list_dir")


def task_tray(root: str, role: str, index: int) -> str:
    """タスクの作業区画を用意して返す（`<root>/<role>/task-N/`。N は1始まり）。"""
    p = Path(root) / role / f"task-{index + 1}"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def copy_in(tray: str, files: Sequence[str]) -> list:
    """共有空間の files を tray へ写す（スナップショット）。写せなかったものを返す。

    needs はゲート（`unmet_needs`）通過後なので、基本ここで欠けることはない——
    欠けたら（産出タスクが done なのに実ファイルが無い等）正直に返し、呼び出し側が
    タスクを失敗させる。絶対パスは共有空間の名前構造を保てないので写さない（宣言は
    作業ディレクトリからの相対パスで行う契約）。
    """
    missing = []
    for f in files:
        src = Path(f)
        if src.is_absolute() or not src.is_file():
            missing.append(f)
            continue
        dst = Path(tray) / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        _remove(dst)   # 前回試行の写しが読み取り専用でも、写しは毎回作り直す（031 実走で実発火:
        shutil.copyfile(src, dst)   # 実行者が skill「入力は読み取り専用」に従い写しに +R を立てた）
    return missing


def _remove(path: Path) -> None:
    """既存ファイルを属性に関わらず消す（Windows は読み取り専用だと unlink も open('wb') も失敗する）。"""
    if path.is_file():
        path.chmod(0o666)
        path.unlink()


def discard_stale_output(tray: str, file: str) -> None:
    """前回試行が tray に残した宣言済み出力を消す（残骸の発行を防ぐ。scratch は残す）。"""
    if not Path(file).is_absolute():
        _remove(Path(tray) / file)


def publish(tray: str, file: str, role: str, owner: str) -> tuple[bool, str]:
    """tray の成果物を共有空間へ発行する。single-writer（師匠宣言）はここで強制する。

    返り値は (発行できたか, 拒否の理由)。拒否はタスクの正直な失敗として PjM に乗る。
    """
    if role != owner:
        return False, (
            f"出力 {file} の書き手は役割 '{owner}' に固定されている"
            f"（'{role}' は発行できない。出力ファイルを共有するプロセスは組めない）"
        )
    if Path(file).is_absolute():
        return False, f"出力 {file} が絶対パスである（共有空間の外には発行できない）"
    src = Path(tray) / file
    if not src.is_file():
        return False, f"宣言した出力 {file} が作業ディレクトリに無い（タスクは出力を産出していない）"
    dst = Path(file)
    if dst.parent != Path("."):
        dst.parent.mkdir(parents=True, exist_ok=True)
    _remove(dst)   # 自分の成果物の前版が読み取り専用でも、正当な発行は通す（所有権は上で検査済み）
    shutil.copyfile(src, dst)
    return True, ""


def tray_tools(tools: Sequence[Tool], tray: str, log: Callable) -> list:
    """ツール群を tray に閉じる（合意030 の読み取りゲート）。

    - パスを取るツール: 相対パスは tray 起点に解決。解決先が tray の外なら拒否
      （読み取り系だけはシステム一時ディレクトリも可——合意010 の観測契約を殺さない）
    - execute_command: tray を作業ディレクトリにして実行する
    - それ以外（web_search / fetch_url 等）: 素通し

    役割の権限（`role_tools`）はこの**外側**に巻く——権限の判定は宣言されたままの
    パス（相対）で行われ、解決はこの層が最後に行う。
    """
    out = []
    for func, usage in tools:
        if func.__name__ in _PATH_TOOLS:
            out.append((_confined(func, tray, log), usage))
        elif func.__name__ == "execute_command":
            out.append((_exec_in(func, tray), usage))
        else:
            out.append((func, usage))
    return out


def _within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _confined(func: Callable, tray: str, log: Callable) -> Callable:
    # read_file だけは temp **直下**のファイルも読める（execute_command の全文保存を辿る
    # 合意010 の契約）。直下限定＝temp 配下の他の作業領域までは開けない。
    temp_ok = func.__name__ == "read_file"

    @wraps(func)
    def confined(path: str = ".", *args, **kwargs):
        p = Path(path)
        base = Path(tray).resolve()
        if p.is_absolute():
            resolved = p.resolve()
        else:
            # 030 bugfix 実走の観測: モデルは作業ディレクトリの案内を見て、共有 cwd からの
            # 相対で「.mu-work/<role>/task-N/file」と tray を名指しすることがある。tray 起点で
            # 解決すると二重入れ子（tray/.mu-work/.../file）になり、書けてしまう（tray 内なので
            # 拒否されない）が置き場所が違い、Reflect の書き直しループを生む。
            # 共有 cwd 起点の解決が tray 内に落ちるならそれを意図とみなす——採るのはどちらの
            # 解釈でも tray 内だけなので、閉じ込めは弱まらない。
            alt = (Path.cwd() / p).resolve()
            resolved = alt if _within(alt, base) else (Path(tray) / p).resolve()
        allowed = _within(resolved, base) or (
            temp_ok and resolved.parent == Path(tempfile.gettempdir()).resolve()
        )
        if not allowed:
            log(("tray_denied", func.__name__, str(path)))
            return ToolResult(
                f"error: このタスクの作業ディレクトリは {tray} に閉じている"
                f"（{path} へは触れない）。相対パスで作業ディレクトリ内を使うこと。"
                "読みたい入力がここに無ければ、それはこのタスクに宣言されていない——"
                "タスクの記述にある参照ファイルだけを使う。",
                ok=False,
                facts={"action": func.__name__, "path": str(path), "denied": True},
            )
        return func(str(resolved), *args, **kwargs)

    return confined


def _exec_in(func: Callable, tray: str) -> Callable:
    @wraps(func)
    def confined(command: str):
        # 実行の作業ディレクトリを tray にする。プロセス cwd は動かさない（大域状態を
        # 避ける——並列実行がそのまま載る形）。前置はコマンドの事実としてログに残る。
        return func(f'Set-Location -LiteralPath "{tray}"; {command}')

    return confined
