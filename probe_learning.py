r"""probe_learning.py — L6（学習の層）の中核能力＝診断を、機構ゼロで単体測定する probe。

合意033。**L6 は作らない。** 学習者（カタログ級定義書 `roles/learner.md`）に過去の走行記録の
材料を渡し、**構造化出力の1判断**で診断させ、確定済みの診断（台帳 `ledger/`。人間の承認を
経たもの）と照合する。028「選択のみ精度」と同型——判断の座を新設するときは、材料を整えて
1判断で測る。

条件（1ケースにつき2つ）:
  R（再発検知）: 台帳に該当モードを**含めて**渡す → 正解 = そのモード名（**機械照合**）
  N（新モード診断）: 台帳から該当モードを**抜いて**渡す → 正解 = new_mode ＋機構の記述
     （機構の一致は人間採点。学習者が「最も近い既存モード」へ無理に寄せないかを見る）

材料の軸（仮説「診断の質は判断文でなく材料の質で決まる」の検証）:
  thin : 仕様・計画・判定の眺め（[tool] 行を除いた実況）
  thick: thin ＋ ツール呼び出しの列——機構の診断にはこれが必須、が事前の仮説

リーク対策（床）: 学習者に渡すのは**生ログからの抽出だけ**。スプリント記録・runs/README は
診断の答えを明記しているため、材料生成の入力にすら使わない。

使い方:
    .\.venv\Scripts\python.exe probe_learning.py list
    .\.venv\Scripts\python.exe probe_learning.py dump <case> [thin|thick] [R|N]
        …学習者に渡る入力（system＋user）を**そのまま**印字する。実走の前に必ず1回見る
          （skill: 結論を出す前に、エージェントが実際に受け取った入力を実物で見る）
    .\.venv\Scripts\python.exe probe_learning.py run <case|all> [model] [reps]
        …live 測定。1判断ごとに JSON 1行を出力する（採点・集計は走の外で行う）
"""

import json
import re
import sys
from pathlib import Path

from mu.l0 import OllamaInterface, L0Error
from mu.l3 import structured
from mu.l4 import lifeline_system
from mu.role_kb import parse_role_doc

REPO = Path(__file__).resolve().parent
LEDGER_DIR = REPO / "ledger"
LEARNER_DOC = REPO / "roles" / "learner.md"
DEFAULT_MODEL = "gemma4:31b-cloud"

# 材料の上限（学習者の context 予算の床）。超えたら**中央を**落とす——冒頭（目的・仕様）と
# 末尾（結果・判定）は診断の目的に直結するため残す（skill: 切る順序を目的に接地させる）。
MAX_CHARS = 60_000

# --- 正解ケース（gold = ledger のモード名。診断は人間の承認を経たもの） -----------
#
# slice の end マーカーは「その走だけを見せる」ため（多ラウンドのログで後続周が答えを
# 漏らすのを防ぐ）。log は**生ログのみ**——記録 README は使わない（リーク）。

CASES = {
    "qa-self-fix": {
        "log": "runs/2026-08-02-007/f1-12b.log",
        "gold": "qa-self-fix-self-approve",
    },
    "checker-overwritten": {
        "log": "runs/2026-08-05-012/research.log",
        "gold": "checker-becomes-the-artifact",
    },
    "protection-escalation": {
        "log": "runs/2026-08-07-017/regression.log",
        "gold": "denied-becomes-an-obstacle",
    },
    "contract-loss": {
        "log": "runs/2026-08-08-019/deadstock.log",
        "gold": "contract-lost-in-transcription",
    },
    "quantifier": {
        "log": "runs/2026-08-10-020/runtime.log",
        "gold": "quantifier-weakening",
    },
    "invented-calls": {
        "log": "runs/2026-08-10-021/schedule.log",
        "gold": "invented-invocations",
    },
    "service-guessing": {
        "log": "runs/2026-08-12-028/auto-schedule.log",
        "gold": "blind-service-trial-and-error",
    },
    "regenerate-loss": {
        "log": "runs/2026-08-13-032/standing-R0-grounded.log",
        "gold": "regenerate-loses-the-document",
    },
    "grounding-drop": {
        "log": "runs/2026-08-13-032/standing.log",
        "gold": "grounding-cap-drops-the-subject",
        "end": "=== R1 ===",     # R0 だけを見せる（後続周は同じ答えの繰り返し）
    },
}

_DIAG_SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {"type": "string"},        # 台帳のモード名。該当なしは ""
        "new_mode": {"type": "boolean"},   # 既知のどのモードでもない
        "mechanism": {"type": "string"},   # 機械的に何が起きたか（1〜3文）
        "evidence": {"type": "string"},    # 記録のどこがそれを示すか（引用・行の名指し）
    },
    "required": ["mode", "new_mode", "mechanism", "evidence"],
}

# --- 台帳と材料（決定論の部品。テスト対象） -------------------------------------

def load_ledger(path: Path = LEDGER_DIR) -> dict:
    """台帳を読む。{モード名: {name, description, maturity, prompt(本文), ...}}。"""
    entries = {}
    for f in sorted(path.glob("*.md")):
        doc = parse_role_doc(f.read_text(encoding="utf-8"))
        entries[str(doc.get("name") or f.stem)] = doc
    return entries


def ledger_lines(ledger: dict, exclude: str = "") -> str:
    """学習者に見せる既知モードの一覧（1行＝「- 名前: 説明」）。N 条件は該当モードを抜く。"""
    lines = [f"- {name}: {doc.get('description', '')}"
             for name, doc in ledger.items() if name != exclude]
    return "\n".join(lines) or "(none)"


_NOISE = re.compile(r"\[L[12]\] (思考中|Reflect（合否）判定中)")


def materials(log_text: str, kind: str) -> str:
    """生ログから学習者に見せる材料を作る。

    thick: 実況からタイミングノイズ（思考中… の行）だけを落としたもの
    thin : thick からさらに [tool] 行（呼び出しと結果）を落としたもの
           ＝仕様・計画・判定の眺め。機構の証拠が消える、が事前の仮説
    """
    lines = [l for l in log_text.splitlines() if not _NOISE.search(l)]
    if kind == "thin":
        lines = [l for l in lines if "[tool]" not in l]
    text = "\n".join(lines)
    if len(text) > MAX_CHARS:
        head, tail = text[: MAX_CHARS // 2], text[-MAX_CHARS // 2:]
        text = (f"{head}\n\n…（中略: 材料の上限 {MAX_CHARS} 字を超えたため中央を省略。"
                f"冒頭と末尾は完全）…\n\n{tail}")
    return text


def case_text(case: dict) -> str:
    """ケースの生ログを読み、slice（その走だけ）を切り出す。"""
    text = (REPO / case["log"]).read_text(encoding="utf-8", errors="replace")
    if case.get("end") and case["end"] in text:
        text = text.split(case["end"])[0]
    return text


def build_input(case: dict, kind: str, condition: str, ledger: dict) -> tuple:
    """学習者に渡す (system, user) を組む。R=台帳に正解あり / N=正解を抜く。"""
    exclude = case["gold"] if condition == "N" else ""
    doc = parse_role_doc(LEARNER_DOC.read_text(encoding="utf-8"))
    system = lifeline_system({"learner": doc}, "learner", "diagnose",
                             _DIAG_SCHEMA, None, lambda e: None)
    user = (
        f"LEDGER (known failure modes):\n{ledger_lines(ledger, exclude)}\n\n"
        f"RUN RECORD (material={kind}; raw console transcript of one completed run):\n"
        f"{materials(case_text(case), kind)}"
    )
    return system, user


# --- 実行 -----------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    ledger = load_ledger()

    if cmd == "list":
        for name, case in CASES.items():
            ok = (REPO / case["log"]).is_file()
            gold_ok = case["gold"] in ledger
            print(f"  {name:22} gold={case['gold']:38} log={'ok' if ok else 'MISSING'} "
                  f"ledger={'ok' if gold_ok else 'MISSING'}")
        return

    if cmd == "dump":
        case = CASES[sys.argv[2]]
        kind = sys.argv[3] if len(sys.argv) > 3 else "thick"
        condition = sys.argv[4] if len(sys.argv) > 4 else "R"
        system, user = build_input(case, kind, condition, ledger)
        print(f"===== SYSTEM ({len(system)} chars) =====\n{system}\n")
        print(f"===== USER ({len(user)} chars) =====\n{user}")
        return

    if cmd == "run":
        target = sys.argv[2]
        model = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_MODEL
        reps = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        names = list(CASES) if target == "all" else [target]
        l0 = OllamaInterface()
        for name in names:
            case = CASES[name]
            for condition in ("R", "N"):
                for kind in ("thin", "thick"):
                    for rep in range(reps):
                        system, user = build_input(case, kind, condition, ledger)
                        try:
                            data = structured(l0, model, system, user, _DIAG_SCHEMA)
                        except L0Error as e:
                            data = {"error": f"{type(e).__name__}: {e}"}
                        record = {
                            "case": name, "condition": condition, "material": kind,
                            "rep": rep, "gold": case["gold"],
                            # R の正解は機械照合できる。N の mechanism は人間採点
                            "hit": (data.get("mode") == case["gold"]) if condition == "R"
                                   else (data.get("mode") == "" and bool(data.get("new_mode"))),
                            **{k: data.get(k) for k in
                               ("mode", "new_mode", "mechanism", "evidence", "error")},
                        }
                        print(json.dumps(record, ensure_ascii=False), flush=True)
        return

    print(__doc__)
    sys.exit(2)


if __name__ == "__main__":
    main()
