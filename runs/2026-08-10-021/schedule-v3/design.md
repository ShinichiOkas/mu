# Design Document: Scheduling '企画会議'

## 1. Analysis of Availability
Target members: 佐藤 (Sato), 鈴木 (Suzuki), 高橋 (Takahashi)
Time window: 2026-08-17 to 2026-08-21, 09:00-17:00
Required duration: 60 minutes

### Daily Slot Analysis:
- **2026-08-17**: 
  - Sato: 12:00-13:00 free.
  - Suzuki: 13:00-14:00 free.
  - Takahashi: 09:00-12:00, 14:00-15:00 free.
  - Common: None.
- **2026-08-18**:
  - Sato: 09:00-11:00 free.
  - Suzuki: Busy all day (研修).
  - Common: None.
- **2026-08-19**:
  - Sato: Busy all day (出張).
  - Common: None.
- **2026-08-20**:
  - Sato: 15:00-16:00 free.
  - Suzuki: 10:30-11:00, 15:00-17:00 free.
  - Takahashi: 12:00-16:00 free.
  - **Common: 15:00 - 16:00** (Sato free 15-16, Suzuki free 15-17, Takahashi free 12-16).
- **2026-08-21**:
  - Takahashi: Busy all day (休暇).
  - Common: None.

### Selected Slot:
- **Date**: 2026-08-20
- **Start Time**: 15:00
- **End Time**: 16:00
- **Event Name**: 企画会議

## 2. Structure
The task is a design specification for an implementation task. The implementation will use the `outlook.py` script to perform the booking.

### Data Flow:
1. Input: `calendar_data.json` (already analyzed).
2. Action: Execute `outlook.py` with specific arguments.
3. Output: Success log in `booking_log.txt` and updated `bookings.json`.

### Responsibility:
- **Architect**: Identify the common free slot and define the booking command.
- **Implementer**: Execute the provided command and verify the result.

## 3. Quality Characteristics and Implementation Structure
To ensure the booking is correctly performed and verifiable:
- **Verification**: The implementation must execute the command and check if the event "企画会議" appears in `bookings.json`.
- **Marker**: The implementation script must print `[BOOKING_SUCCESS]` upon successful verification of the entry in `bookings.json`.

## 4. Design Rules
- **Read-Only Inputs**: `calendar_data.json` and `outlook.py` must be treated as read-only.
- **Artifacts**: Only `bookings.json` and `booking_log.txt` should be modified/created as results of the booking.
- **Command Accuracy**: The following exact command must be used:
  `python outlook.py --book "2026-08-20 15:00" "2026-08-20 16:00" "企画会議" "佐藤,鈴木,高橋"`

## 5. Booking Specification
- **Event**: 企画会議
- **Start**: 2026-08-20 15:00
- **End**: 2026-08-20 16:00
- **Attendees**: 佐藤, 鈴木, 高橋
- **Booking Command**:
  `python outlook.py --book "2026-08-20 15:00" "2026-08-20 16:00" "企画会議" "佐藤,鈴木,高橋"`
