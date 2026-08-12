"""mu/workspace.py（作業空間＝tray の facility）のユニットテスト（合意030）。

守るのはコードの決定論: copy-in のスナップショット・ツールの tray 閉じ込め・
publish-out と single-writer の発行ゲート。師匠の宣言「入出力ファイルは共有空間、
作業ファイルは個別ディレクトリ、出力の書き手は1ロール固定」の機構化。
"""

import tempfile
from pathlib import Path

import tools
from mu.workspace import (
    copy_in, discard_stale_output, publish, task_tray, tray_tools,
)


def _wrapped(tray, name):
    wrapped = tray_tools(list(tools.TOOLS), str(tray), lambda e: None)
    return next(f for f, _ in wrapped if f.__name__ == name)


# --- tray と copy-in -----------------------------------------------------------

def test_task_tray_is_per_role_and_per_task(tmp_path):
    a = task_tray(str(tmp_path / "work"), "implementer", 0)
    b = task_tray(str(tmp_path / "work"), "implementer", 2)
    c = task_tray(str(tmp_path / "work"), "qa", 2)
    assert a != b and b != c
    assert Path(a).is_dir()
    assert "implementer" in a and "task-1" in a


def test_copy_in_snapshots_the_declared_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "design.md").write_text("v1", encoding="utf-8")
    tray = task_tray("work", "implementer", 0)
    assert copy_in(tray, ["design.md"]) == []
    (tmp_path / "design.md").write_text("v2", encoding="utf-8")   # 共有空間が後で動いても
    assert (Path(tray) / "design.md").read_text(encoding="utf-8") == "v1"   # 写しは不変


def test_copy_in_reports_what_it_could_not_copy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "implementer", 0)
    assert copy_in(tray, ["nosuch.csv"]) == ["nosuch.csv"]


def test_discard_stale_output_removes_only_the_declared_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "implementer", 0)
    (Path(tray) / "out.md").write_text("残骸", encoding="utf-8")
    (Path(tray) / "scratch.txt").write_text("観測のために残す", encoding="utf-8")
    discard_stale_output(tray, "out.md")
    assert not (Path(tray) / "out.md").exists()
    assert (Path(tray) / "scratch.txt").exists()


# --- ツールの閉じ込め（読み取りゲートの構造化） ---------------------------------

def test_relative_paths_resolve_into_the_tray(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "implementer", 0)
    write = _wrapped(tray, "write_file")
    assert write("out.md", "本文").ok
    assert (Path(tray) / "out.md").read_text(encoding="utf-8") == "本文"
    assert not (tmp_path / "out.md").exists()          # 共有空間には書かれない


def test_an_undeclared_shared_file_is_invisible(tmp_path, monkeypatch):
    # 未宣言の依存は「静かなレース」ではなく「読めない」という可視な失敗になる。
    # 素のツールは無いファイルで例外を投げ、L1 の dispatch がそれを結果として
    # モデルに返す（l1.py の try/except）——実ループでは正直な失敗として観測される。
    import pytest
    monkeypatch.chdir(tmp_path)
    (tmp_path / "secret.txt").write_text("共有空間の実物", encoding="utf-8")
    tray = task_tray("work", "implementer", 0)
    read = _wrapped(tray, "read_file")
    with pytest.raises(FileNotFoundError):
        read("secret.txt")                             # tray に写しが無い＝存在しない


def test_absolute_paths_outside_the_tray_are_refused(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "secret.txt").write_text("原本", encoding="utf-8")
    tray = task_tray("work", "implementer", 0)
    events = []
    wrapped = tray_tools(list(tools.TOOLS), str(tray), events.append)
    read = next(f for f, _ in wrapped if f.__name__ == "read_file")
    result = read(str(tmp_path / "secret.txt"))
    assert result.ok is False
    assert "閉じている" in result.content
    assert ("tray_denied", "read_file", str(tmp_path / "secret.txt")) in events


def test_reads_of_the_system_temp_dir_stay_allowed(tmp_path, monkeypatch):
    # 合意010 の観測契約: execute_command の長い出力は一時ファイルに保存され
    # read_file で辿る。閉じ込めがこの経路を殺してはならない。
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "implementer", 0)
    import os
    fd, temp = tempfile.mkstemp(prefix="mu-exec-", suffix=".txt")
    os.close(fd)
    Path(temp).write_text("長い出力の全文", encoding="utf-8")
    read = _wrapped(tray, "read_file")
    assert read(temp).ok
    assert not _wrapped(tray, "write_file")(temp, "x").ok   # 書き込みは tray だけ


def test_execute_command_runs_inside_the_tray(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "implementer", 0)
    run = _wrapped(tray, "execute_command")
    result = run('Set-Content -Path "made.txt" -Value "x"')
    assert result.ok
    assert (Path(tray) / "made.txt").exists()
    assert not (tmp_path / "made.txt").exists()


def test_tools_without_paths_pass_through(tmp_path):
    tray = task_tray(str(tmp_path / "work"), "implementer", 0)
    wrapped = tray_tools(list(tools.TOOLS), tray, lambda e: None)
    assert {f.__name__ for f, _ in wrapped} == {f.__name__ for f, _ in tools.TOOLS}


# --- publish-out と single-writer ----------------------------------------------

def test_publish_copies_the_output_to_the_shared_space(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "writer", 0)
    (Path(tray) / "story.md").write_text("初稿", encoding="utf-8")
    ok, reason = publish(tray, "story.md", "writer", "writer")
    assert ok and reason == ""
    assert (tmp_path / "story.md").read_text(encoding="utf-8") == "初稿"


def test_publish_refuses_a_nonowner_role(tmp_path, monkeypatch):
    # 師匠宣言: 出力ファイルの書き手は1ロールに固定。宣言はデータ・適用はコード。
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "editor", 0)
    (Path(tray) / "story.md").write_text("勝手な書き直し", encoding="utf-8")
    ok, reason = publish(tray, "story.md", "editor", "writer")
    assert ok is False
    assert "writer" in reason and "固定" in reason
    assert not (tmp_path / "story.md").exists()        # 共有空間は汚れない


def test_publish_refuses_when_the_declared_output_was_not_produced(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tray = task_tray("work", "implementer", 0)
    ok, reason = publish(tray, "result.csv", "implementer", "implementer")
    assert ok is False
    assert "産出していない" in reason
