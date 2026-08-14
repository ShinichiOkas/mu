# mu-standing

A multi-layered LLM agent architecture designed for robust goal achievement through recursive PDCA loops.

## Architecture Overview

The system is structured into six layers (L0 to L5), each with a specific responsibility to ensure stability, autonomy, and alignment with high-level purposes.

### L0: Ollama Interface Layer
**Responsibility:** Stabilize and idealize the connection to the LLM.
- Acts as the innermost layer.
- Absorbs connection errors, timeouts, and model availability issues.
- Presents a simplified, idealized LLM interface to higher layers.
- Maps complex errors into four types: `Unreachable`, `ModelUnavailable`, `ResourceExhausted`, `BadRequest`.

### L1: Tool Call Loop (Do)
**Responsibility:** Execute tool calls in a loop.
- Implements the basic "Chat → Tool Call → Execute → Feed back" cycle.
- Stateless: Maintains no internal state; messages are managed by higher layers.
- Handles tool schema generation and dispatching.

### L2: Reflect Loop (Agent)
**Responsibility:** Achieve a single checkable goal using a PDCA cycle.
- Wraps L1 in a "Reflect (Check + Act)" loop.
- Cycle: Do (L1) $\rightarrow$ Reflect (Check if goal is met) $\rightarrow$ Act (Re-plan if needed).
- Recursive structure: This loop pattern is mirrored at higher layers.

### L3: Global Plan (Orchestrator)
**Responsibility:** Complete complex goals by combining L2 units.
- Explicitly manages a global plan to decompose complex goals into checkable units.
- Uses file-grounding: Each unit produces a tangible artifact.
- Verification: Mechanically checks if all units are completed.

### L4: Progress Layer (PjM / Manager)
**Responsibility:** Define and manage the process of execution.
- Translates a specification (SPEC) into a sequence of tasks with role annotations.
- Manages "Role-based L3 units" to complete tasks.
- Handles internal failures (rerun/replan) and escalates specification issues to L5.

### L5: Purpose Layer (PdM / Director)
**Responsibility:** Translate human purpose into operational specifications.
- Bridges the gap between natural language purpose and detailed SPEC.
- Manages L4 and decides whether to accept the final result, revise the specification (respec), or escalate to a human.

## Core Files

- `l0.py` to `l5.py`: Core logic for each layer.
- `l0_chat.py` to `l5_chat.py`: Chat interfaces for interacting with each layer.

## Implementation Details

The architecture follows the principle of "Decision outside, Execution inside," where higher layers define the goals and constraints, while lower layers execute the actions.
