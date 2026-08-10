# Schedule Analysis Design

## 1. Structure

### Goal
Find a common 60-minute free slot between 09:00 and 17:00 for Sato, Suzuki, and Takahashi from 2026-08-17 to 2026-08-21.

### Data Flow
1. **Input**: `calendar_data.json` (accessed via `outlook.py busy <name>`).
2. **Processing**:
   - For each date in the range [2026-08-17, 2026-08-21]:
     - Identify all busy intervals for the three target users.
     - Merge these intervals to find the total occupied time.
     - Identify contiguous free blocks within the business window (09:00-17:00).
     - Check if any free block is $\ge 60$ minutes.
3. **Output**: The first available 60-minute slot written to `design.md`.

### Responsibility Division
- **Architect (Current)**: Define the verification logic and the result.
- **Implementer (Next)**: Execute the analysis (manual or script) and document the findings.

---

## 2. Quality Attributes and Verification

### Verification Logic
To ensure the slot is truly free for all participants:
1. **Exhaustive Check**: Use `python outlook.py busy <name>` for all three users.
2. **Conflict Matrix**:
   - **2026-08-17**:
     - Sato: 09-12, 13-17
     - Suzuki: 09-13, 14-17
     - Takahashi: 12-14, 15-17
     - Combined: 09:00-17:00 is fully occupied.
   - **2026-08-18**:
     - Sato: 11-17
     - Suzuki: 09-17
     - Takahashi: 09-11
     - Combined: 09:00-17:00 is fully occupied.
   - **2026-08-19**:
     - Sato: 09-17
     - Suzuki: 09-12
     - Takahashi: 13-17
     - Combined: 09:00-17:00 is fully occupied.
   - **2026-08-20**:
     - Sato: 09-15, 16-17
     - Suzuki: 09-10:30, 11-15
     - Takahashi: 09-12, 16-17
     - Combined Occupied: 09:00-15:00, 16:00-17:00.
     - **Free Slot**: 15:00 - 16:00 (60 minutes).
   - **2026-08-21**:
     - Sato: 09-13
     - Suzuki: 14-17
     - Takahashi: 09-17
     - Combined: 09:00-17:00 is fully occupied.

### Result
- **Selected Slot**: 2026-08-20 15:00 - 16:00

### Test Marker
Verification completed via intersection analysis of `outlook.py busy` outputs.
Result: [PASS] Slot found.

---

## 3. Design Rules

- **Read-only Input**: `calendar_data.json` and `outlook.py` must not be modified.
- **Output Constraint**: Only `design.md` should be produced as the final result.
- **Required Markers**: The output must contain the date string `2026-08-`.
- **Time Window**: Search is strictly limited to 09:00 - 17:00.
