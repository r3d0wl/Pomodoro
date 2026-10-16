# Python Pomodoro Timer Desktop App

A customizable, multi-tab desktop Pomodoro timer built in Python using `tkinter` and `ttk.Notebook`. Designed with a clean separation between state-machine logic and UI components to support future styling upgrades.

## Features

* **Three Dedicated Mode Tabs:** Separate tabs for **Pomodoro** (Focus), **Short Break**, and **Long Break**.
* **Per-Tab Customization:** Each tab includes a `Spinbox` input allowing users to customize durations (1–120 minutes) via arrow buttons, pressing `Enter`, or clicking away.
* **Automated 4-Pomodoro Cycle:** Tracks completed focus sessions (`0/4` to `4/4`). Completing Pomodoros 1–3 automatically routes the user to the **Short Break** tab; completing the 4th Pomodoro triggers a **30-minute Long Break** and resets the cycle counter afterward.
* **Single Active Timer Guard:** Starting a timer on one tab automatically pauses any running timer on other tabs to prevent concurrent countdown conflicts.
* **Non-Blocking Event Loop:** Uses Tkinter's `.after()` scheduling rather than `time.sleep()` so the interface remains responsive during countdowns.

---

## Project Architecture

1. **`TimerTab(ttk.Frame)`:** A reusable view-controller component representing an individual tab. Manages its own countdown display, custom minute validation, and `Start` / `Pause` / `Reset` state.
2. **`PomodoroApp`:** The main application controller. Manages the top-level window, the `ttk.Notebook` tab container, cross-tab pause synchronization (`stop_all_timers`), and the 4-Pomodoro cycle counter.

---

## Troubleshooting & Bug Fixes Log (Breaks Encountered)

During initial development and testing, several runtime errors and logic bugs were identified and resolved:

### 1. Application Crash on Launch (`_tkinter.TclError`)
* **The Break:** Running the script immediately threw `_tkinter.TclError: unknown option "-weight"` inside `TimerTab.create_widgets()`.
* **Root Cause:** `weight="bold"` was passed as a standalone keyword argument to `ttk.Label`, which Tkinter does not support.
* **The Fix:** Moved the `"bold"` style modifier inside the `font` tuple: `font=("Helvetica", 48, "bold")`.

### 2. Custom Duration Reverting on Reset
* **The Break:** Changing the minutes in the `Spinbox` updated the display initially, but clicking the **Reset** button forced the clock back to the original default value instead of keeping the user's custom time.
* **Root Cause:** Inside `apply_custom_time()`, the statement `self.default_minutes` was written on a line without an assignment (`= mins`), leaving the baseline attribute unchanged.
* **The Fix:** Completed the assignment (`self.default_minutes = mins`) after validating that the input was a positive integer.

### 3. Pausing and Resuming Erased Countdown Progress
* **The Break:** Starting a timer, letting it count down, clicking **Pause**, and clicking **Start** again caused the clock to jump back to the full starting duration instead of resuming from where it paused.
* **Root Cause:** `toggle_timer()` called `self.apply_custom_time()` every time the timer started, which recalculated `self.remaining_seconds = mins * 60` unconditionally.
* **The Fix:** Added a guard condition (`if mins != self.default_minutes:`) inside `apply_custom_time()` so the remaining seconds are only overwritten when the user actually changes the Spinbox value or clicks **Reset**.


---

## Testing the Application

Because testing a full 4-Pomodoro cycle in real time takes over two hours, three verification methods were used:

1. **Time-Warp Manual Testing:** Temporarily lowering the `.after(1000, self.countdown)` interval to `10` milliseconds (100x speed) to visually verify tab transitions, Spinbox locking, and dialog popups in under 5 seconds.
2. **Automated Unit Testing (`test_pomodoro.py`):** Built a 5-test suite using Python's `unittest` and `unittest.mock.patch` (to silence GUI modal dialogs during headless execution). Verified initial default durations (`30m`/`10m`/`45m`), the full 4-Pomodoro routing cycle, custom Spinbox validation, pause/resume progress preservation, and single-active-timer enforcement.
3. **Input Validation Checks:** Testing negative numbers, zero, and non-numeric strings (`"abc"`) in the Spinbox to confirm the `ValueError` handler safely reverts to the last valid minute setting.

---

## How to Run

Ensure Python 3 is installed, then run:

```bash
python pomodoroapp.py