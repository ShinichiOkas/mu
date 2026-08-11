"""028 C: 選択のみの精度計測——6目的（5ドメイン既知課題＋適合なし1件）×3反復。

目的文は probe の実物（probe_hard.CASES / probe_research._RUNTIME_PURPOSE）から取り、
e2e と同一テキストを保証する。適合なしの負例は画像制作（カタログのどの職掌でもない）。
"""

import sys
import time

sys.path.insert(0, r"s:\work\develop\mu")

from chat_common import auto_catalog
from mu.l0 import OllamaInterface
from mu.l5 import Director
from probe_hard import CASES
from probe_research import _RUNTIME_PURPOSE

MODEL = "gemma4:31b-cloud"
REPS = 3
PURPOSES = [
    ("coding", CASES["bugfix"]["purpose"]),
    ("research", _RUNTIME_PURPOSE),
    ("secretary", CASES["schedule"]["purpose"]),
    ("rnd", CASES["rnd"]["purpose"]),
    ("book", CASES["book"]["purpose"]),
    ("", "会社の新しいロゴ画像をデザインして、PNG ファイルで納品してくれ。"),
]

packages, selector = auto_catalog()
director = Director(OllamaInterface())
ok_count, total = 0, 0
for expected, purpose in PURPOSES:
    for rep in range(1, REPS + 1):
        t0 = time.monotonic()
        sel = director._select_package(MODEL, purpose, packages, selector, lambda e: None, None)
        got = sel.get("package", "")
        ok = got == expected
        ok_count += ok
        total += 1
        note = sel.get("escalate", "")[:100] if "escalate" in sel else ""
        print(f"expected={(expected or '(none)'):10}  rep={rep}  "
              f"got={(got or '(escalate)'):10}  {'OK' if ok else 'NG'}  "
              f"({time.monotonic() - t0:.1f}s)  {note}", flush=True)

print(f"\naccuracy: {ok_count}/{total}")
