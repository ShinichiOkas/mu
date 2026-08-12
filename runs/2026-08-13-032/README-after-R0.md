# Project Documentation

## Layer Mappings (L0-L5)

The system is structured into six hierarchical layers, each with a distinct role:

- **L0 (Ollama Interface Layer)**: Idealized LLM interface, handles retries and maps failures.
- **L1 (Tool Call Loop)**: "Do" layer, manages chat-tool-execute loop.
- **L2 (PDCA / Reflect Loop)**: Agent layer, implements Reflect cycle (Check + Act).
- **L3 (Global Plan / Orchestrator)**: Complex task completion, explicit global planning (P-D-C-A).
- **L4 (Progress Layer / PjM)**: Manages project progress (SPEC -> PROCESS -> L3).
- **L5 (Purpose Layer / PdM)**: Bridges human purpose to SPEC.md.

## Major Executable Files

The following files are the primary entry points and tools for the system:

- `l0_chat.py`
- `l1_chat.py`
- `l2_chat.py`
- `l3_chat.py`
- `l4_chat.py`
- `l5_chat.py`
- `probe_hard.py`
- `probe_research.py`
- `probe_standing.py`
