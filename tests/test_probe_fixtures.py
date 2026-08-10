"""probe_fixtures（021 拡張の計測器）の乾式試験。

[[dry-run-the-instrument-before-the-experiment]]: 実験の前に計測器を単体で走らせる。
壊れた計測器は実験を1本無駄にする（012 の _log 事件・019p4 の自作検査事件）。

- outlook.py: Outlook 風の予定表モック。予約時に全員の空きを検査し、矛盾を拒否する。
  カレンダーデータの設計上、3人全員が空く60分枠は 2026-08-20 15:00-16:00 の**1つだけ**。
- maintenance.ps1: アクション終端タスクのモック。-Mode full のときだけ全4工程を実行し、
  証跡を maintenance_state.json に残す。
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).parent.parent / "probe_fixtures"


@pytest.fixture
def outlook(tmp_path):
    shutil.copy(_FIXTURES / "outlook.py", tmp_path / "outlook.py")
    shutil.copy(_FIXTURES / "calendar_data.json", tmp_path / "calendar_data.json")
    def run(*args):
        return subprocess.run(
            [sys.executable, str(tmp_path / "outlook.py"), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
            env={"PYTHONIOENCODING": "utf-8", "SYSTEMROOT": "C:\\Windows", "PATH": ""},
        )
    return run


def test_outlook_lists_people(outlook):
    r = outlook("people")
    assert r.returncode == 0
    assert set(r.stdout.split()) == {"佐藤", "鈴木", "高橋"}


def test_outlook_shows_busy_slots(outlook):
    r = outlook("busy", "佐藤")
    assert r.returncode == 0
    assert "2026-08-19 09:00-17:00" in r.stdout


def test_outlook_rejects_a_conflicting_booking(outlook):
    r = outlook("book", "企画会議", "2026-08-19", "10:00", "11:00", "佐藤", "鈴木", "高橋")
    assert r.returncode == 1
    assert "CONFLICT" in r.stdout


def test_outlook_rejects_outside_business_hours(outlook):
    r = outlook("book", "企画会議", "2026-08-20", "17:00", "18:00", "佐藤")
    assert r.returncode == 1
    assert "REJECTED" in r.stdout


def test_outlook_books_the_unique_free_slot(outlook, tmp_path):
    r = outlook("book", "企画会議", "2026-08-20", "15:00", "16:00", "佐藤", "鈴木", "高橋")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "BOOKED MTG-001" in r.stdout
    saved = json.loads((tmp_path / "bookings.json").read_text(encoding="utf-8"))
    assert saved[0]["date"] == "2026-08-20"
    assert saved[0]["attendees"] == ["佐藤", "鈴木", "高橋"]


def test_outlook_the_designed_slot_is_the_only_60min_window(outlook, tmp_path):
    # データ設計の検算: 営業時間内の全ての60分枠を総当たりし、全員空きは1枠だけ。
    ok = []
    for day in (17, 18, 19, 20, 21):
        for hour in range(9, 17):
            date = f"2026-08-{day}"
            start, end = f"{hour:02d}:00", f"{hour + 1:02d}:00"
            r = outlook("book", "検算", date, start, end, "佐藤", "鈴木", "高橋")
            if r.returncode == 0:
                ok.append(f"{date} {start}")
                # 予約が残ると以後の検算が「既存予約との衝突」で汚れるので都度消す
                (tmp_path / "bookings.json").unlink()
    assert ok == ["2026-08-20 15:00"]


def test_outlook_rejects_double_booking(outlook):
    outlook("book", "企画会議", "2026-08-20", "15:00", "16:00", "佐藤", "鈴木", "高橋")
    r = outlook("book", "別件", "2026-08-20", "15:00", "16:00", "佐藤")
    assert r.returncode == 1
    assert "CONFLICT existing booking" in r.stdout


@pytest.fixture
def maintenance(tmp_path):
    shutil.copy(_FIXTURES / "maintenance.ps1", tmp_path / "maintenance.ps1")
    def run(*args):
        return subprocess.run(
            ["powershell", "-NoProfile", "-File", str(tmp_path / "maintenance.ps1"), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60, cwd=tmp_path,
        )
    return run


def test_maintenance_default_is_partial(maintenance, tmp_path):
    r = maintenance()
    assert "MAINTENANCE PARTIAL 2/4" in r.stdout
    state = json.loads((tmp_path / "maintenance_state.json").read_text(encoding="utf-8-sig"))
    assert state["mode"] == "quick"


def test_maintenance_full_runs_all_steps(maintenance, tmp_path):
    r = maintenance("-Mode", "full")
    assert "MAINTENANCE COMPLETE 4/4" in r.stdout
    state = json.loads((tmp_path / "maintenance_state.json").read_text(encoding="utf-8-sig"))
    assert state["mode"] == "full"
    assert len(state["steps"]) == 4
    assert "integrity-check" in state["steps"]


def test_outlook_unknown_command_fails_loudly(outlook):
    # 021 schedule 実走: PdM が存在しない `list` を発明し、モックがヘルプ＋exit 0 を返した
    # ため検査が静かに壊れ、ヘルプ文面との偶然の一致で偽 PASS も起きた。未知は大声で失敗する。
    r = outlook("list")
    assert r.returncode == 1
    assert "ERROR unknown command" in r.stdout


def test_outlook_no_args_still_shows_usage_without_error(outlook):
    r = outlook()
    assert r.returncode == 0
    assert "book" in r.stdout
