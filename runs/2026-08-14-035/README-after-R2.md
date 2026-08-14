# Architecture Layers (L0-L5)

This project implements a layered LLM architecture where each layer adds a specific capability to the underlying one.

## Layer Definitions

- **L0: Ollama インタフェース層**
  The base interface layer for interacting with LLMs via Ollama. A stateless "idealized chat" without tools or PDCA loops.
- **L1: ツールコールのループ層**
  Layer that implements the tool-calling loop on top of L0. It allows the model to execute tools and receive results.
- **L2: PDCA / Reflect ループ層**
  Layer that wraps L1 (Do) with a Reflect (Check + Act) loop to autonomously work towards a given goal.
- **L3: 大域 Plan / 複雑タスク完遂層**
  Layer that combines L2 units to complete complex goals. Implements global planning (P) and replanning (A), often involving Human-In-The-Loop (HITL) approval.
- **L4: 進行の層 / PjM**
  Project Management layer. Takes a specification (SPEC), orchestrates a process (PROCESS.md), assigns roles to L3, and evaluates the outcome via deterministic checks and QA verdicts.
- **L5: 目的の層 / PdM**
  Product Management layer. Translates a high-level purpose into operational definitions, acceptance criteria, and a specification (SPEC.md), then triggers the rest of the stack to achieve the purpose.
