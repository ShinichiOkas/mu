"""L1（ツールコールのループ）のユニットテスト。

L0 をフェイクに差し替え、ループの本質（chat→tool_call→実行→chat→…）と、
無状態性（状態 = messages は上位が持つ／中断・再開）を検証する。実サーバは使わない。
"""

import types

from mu.l1 import ToolLoop


class FakeToolCall:
    def __init__(self, name, arguments):
        self.function = types.SimpleNamespace(name=name, arguments=arguments)


class FakeMsg:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeResp:
    def __init__(self, message):
        self.message = message


class FakeL0:
    """step ごとに積んだ応答を返すフェイク L0。渡された引数を記録する。"""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def chat(self, model, messages, **kwargs):
        snap = [
            m if isinstance(m, dict)
            else {"role": getattr(m, "role", "?"), "content": getattr(m, "content", "")}
            for m in messages
        ]
        self.calls.append({"model": model, "messages": snap, "tools": kwargs.get("tools")})
        assert self._responses, "フェイク L0 の応答が尽きた"
        return self._responses.pop(0)


# --- テスト用ツール ---
def add(a: int, b: int) -> int:
    """2 数を足す。"""
    return a + b


def boom() -> str:
    """必ず失敗する。"""
    raise ValueError("nope")


def resp_tool(name, **arguments):
    return FakeResp(FakeMsg(content="", tool_calls=[FakeToolCall(name, arguments)]))


def resp_text(text):
    return FakeResp(FakeMsg(content=text, tool_calls=None))


def test_no_tool_calls_finishes_in_one_step():
    l0 = FakeL0([resp_text("hello")])
    messages, done = ToolLoop(l0).step("m", [{"role": "user", "content": "hi"}], [])
    assert done is True
    assert messages[-1] == {"role": "assistant", "content": "hello"}


def test_tool_call_is_executed_and_loop_continues():
    l0 = FakeL0([resp_tool("add", a=2, b=3), resp_text("the answer is 5")])
    messages = ToolLoop(l0).run("m", [{"role": "user", "content": "2+3?"}], [(add, "add(a,b): 2数を足す")])
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert tool_msgs and tool_msgs[0]["content"] == "5"  # 実際に add が呼ばれた
    assert tool_msgs[0]["tool_name"] == "add"
    assert messages[-1] == {"role": "assistant", "content": "the answer is 5"}
    assert len(l0.calls) == 2  # ループは2周


def test_assistant_tool_call_turn_is_recorded():
    l0 = FakeL0([resp_tool("add", a=1, b=1), resp_text("done")])
    messages = ToolLoop(l0).run("m", [{"role": "user", "content": "x"}], [(add, "add")])
    with_calls = [m for m in messages if m.get("role") == "assistant" and "tool_calls" in m]
    assert with_calls
    assert with_calls[0]["tool_calls"][0]["function"]["name"] == "add"


def test_usage_text_injected_as_system_and_not_persisted():
    l0 = FakeL0([resp_text("ok")])
    out, done = ToolLoop(l0).step("m", [{"role": "user", "content": "hi"}], [(add, "USAGE-MARKER-XYZ")])
    sent = l0.calls[0]["messages"]
    assert sent[0]["role"] == "system"
    assert "USAGE-MARKER-XYZ" in sent[0]["content"]  # usage_text が system に入る
    assert all(m.get("role") != "system" for m in out)  # 永続 messages には残さない（一時注入）
    assert add in (l0.calls[0]["tools"] or [])  # 関数も tools= として渡る


def test_unknown_tool_returns_error_result():
    l0 = FakeL0([resp_tool("ghost"), resp_text("hmm")])
    messages = ToolLoop(l0).run("m", [{"role": "user", "content": "x"}], [(add, "add")])
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert "unknown tool" in tool_msgs[0]["content"]
    assert tool_msgs[0]["tool_name"] == "ghost"


def test_tool_exception_becomes_error_result():
    l0 = FakeL0([resp_tool("boom"), resp_text("recovered")])
    messages = ToolLoop(l0).run("m", [{"role": "user", "content": "x"}], [(boom, "boom(): 失敗する")])
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert tool_msgs[0]["content"] == "error: nope"


def test_empty_tools_is_plain_chat():
    l0 = FakeL0([resp_text("no tools here")])
    _out, done = ToolLoop(l0).step("m", [{"role": "user", "content": "hi"}], [])
    assert done is True
    assert l0.calls[0]["tools"] is None
    assert all(m["role"] != "system" for m in l0.calls[0]["messages"])


def test_unknown_kwarg_is_dropped_and_call_succeeds():
    # モデルがスキーマにない引数（content_type 等）を幻覚しても、シグネチャに
    # 束縛して正しい引数で実行する。厳格な func(**args) は余計な1引数で正しい
    # 呼び出しごと落とし、弱いモデルを無限ループさせていた（実ログで観測）。
    l0 = FakeL0([resp_tool("add", a=2, b=3, content_type="text/plain"), resp_text("done")])
    messages = ToolLoop(l0).run("m", [{"role": "user", "content": "x"}], [(add, "add")])
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert tool_msgs[0]["tool_name"] == "add"
    assert "5" in tool_msgs[0]["content"]             # 正しい引数で実行された
    assert "content_type" in tool_msgs[0]["content"]  # 落とした未知引数は注記される


def test_missing_required_arg_still_errors():
    # 未知引数を落とした結果、本当に必須引数が欠けていれば従来どおりエラー。
    l0 = FakeL0([resp_tool("add", a=2, content_type="x"), resp_text("hmm")])
    messages = ToolLoop(l0).run("m", [{"role": "user", "content": "x"}], [(add, "add")])
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert tool_msgs[0]["content"].startswith("error:")


def test_known_args_only_leaves_result_unannotated():
    # 未知引数が無ければ結果に注記を付けない（既存の tool 結果契約を汚さない）。
    l0 = FakeL0([resp_tool("add", a=2, b=3), resp_text("done")])
    messages = ToolLoop(l0).run("m", [{"role": "user", "content": "x"}], [(add, "add")])
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert tool_msgs[0]["content"] == "5"  # 素の結果のまま（[note] を付けない）


def test_stateless_resume_with_saved_messages():
    # 1周目: ツールを実行して中断（done=False）
    l0a = FakeL0([resp_tool("add", a=4, b=4)])
    saved, done = ToolLoop(l0a).step("m", [{"role": "user", "content": "4+4?"}], [(add, "add")])
    assert done is False
    # 別プロセス相当: 新しい L1 と L0 で、保存した messages から再開
    l0b = FakeL0([resp_text("it is 8")])
    resumed = ToolLoop(l0b).run("m", saved, [(add, "add")])
    assert resumed[-1] == {"role": "assistant", "content": "it is 8"}
    # 再開側の chat は、保存された tool 結果(8)を含む messages を受け取っている
    assert any(m.get("role") == "tool" and m.get("content") == "8" for m in l0b.calls[0]["messages"])
