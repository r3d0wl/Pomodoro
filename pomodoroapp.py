# Testing UI Branch

import os
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class CanvasDotTracker(ttk.Canvas):
    """A custom Canvas widget to display a cycle of filled and empty dots."""

    def __init__(self, parent, dot_count=4, dot_size=16, spacing=12):
        width = (dot_count * dot_size) + ((dot_count - 1) * spacing) + 4
        height = dot_size + 4
        bg_color = ttk.Style().colors.bg 

        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.dot_count = dot_count
        self.dot_size = dot_size
        self.spacing = spacing
        self.current_count = 0
        self.draw_dots()

    def update_count(self, count):
        """Updates the number of filled dots and redraws the canvas."""
        self.current_count = count
        self.draw_dots()

    def draw_dots(self):
        """Draws the filled and empty dots on the canvas."""
        self.delete("all")  # Clear previous drawings
        for i in range(self.dot_count):
            x0 = 2 + i * (self.dot_size + self.spacing)
            y0 = 2
            x1 = x0 + self.dot_size
            y1 = y0 + self.dot_size
            fill_color = "#FF6B6B" if i < self.current_count else "#E0E0E0"
            self.create_oval(x0, y0, x1, y1, fill=fill_color, outline="")
  

class TimerTab(ttk.Frame):
    """A reusable tab component with its own timer display, customization, and controls."""

    def __init__(self, parent, app_controller, title, default_minutes, accent_style, on_complete_callback):
        super().__init__(parent, padding=20)
        self.app_controller = app_controller
        self.title = title
        self.default_minutes = default_minutes
        self.accent_style = accent_style
        self.on_complete_callback = on_complete_callback

        # Timer state variables
        self.remaining_seconds = self.default_minutes * 60  # in seconds
        self.is_running = False
        self.timer_id = None

        # Create UI components
        self.create_widgets()

    def create_widgets(self):
        # 1. Customization Section (Minutes Input)
        settings_frame = ttk.Frame(self)
        settings_frame.pack(pady=(0, 10))

        ttk.Label(settings_frame, text="Set Minutes:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(5))

        self.minutes_var = tk.StringVar(value=str(self.default_minutes))
        self.time_entry = ttk.Entry(
            settings_frame, 
            textvariable=self.minutes_var, 
            width=6, 
            justify="center",
            bootstyle=self.accent_style
        )
        self.time_entry.pack(side=tk.LEFT, padx=5)

        #Bind Enter/Return key to update the timer when typing a custom number
        self.time_entry.bind("<Return>", lambda event: self.apply_custom_time())
        self.time_entry.bind("<FocusOut>", lambda event: self.apply_custom_time())

        # 2. Countdown Display
        self.timer_label = ttk.Label(
            self, 
            text=self.format_time(self.remaining_seconds), 
            font=("Helvetica", 48, "bold"), 
            bootstyle=self.accent_style
        )
        self.timer_label.pack(pady=15)

        # 3. Controls (Start / Pause & Reset)
        controls_frame = ttk.Frame(self)
        controls_frame.pack(pady=10)

        self.start_button = ttk.Button(
            controls_frame, 
            text="Start", 
            bootstyle=self.accent_style,
            width=10,
            command=self.toggle_timer
        )
        self.start_button.pack(side=tk.LEFT, padx=6)

        self.reset_button = ttk.Button(
            controls_frame, 
            text="Reset", 
            bootstyle="secondary-outline",
            command=self.reset_timer
        )
        self.reset_button.pack(side=tk.LEFT, padx=6)

    def format_time(self, total_seconds):
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def apply_custom_time(self):
        """Updates the timer duration based on the custom Spinbox input."""
        if self.is_running:
            return # Prevent changing time while the timer is running
        try:
            mins = int(self.minutes_var.get().strip())
            if mins <= 0:
                raise ValueError
            # Only reset the clock if the minute setting actually changed
            if mins != self.default_minutes:
                self.default_minutes = mins
                self.remaining_seconds = mins * 60
                self.timer_label.config(text=self.format_time(self.remaining_seconds))
        except ValueError:
            # Revert to last valid minute setting if input is invalid
            self.minutes_var.set(str(self.default_minutes))

    def toggle_timer(self):
        """Starts or pauses the timer based on its current state.""" 
        if self.is_running:
            self.pause_timer()
        else:
            # Stop any other tab's timer before starting this one
            self.app_controller.stop_all_timers(except_tab=self)
            self.apply_custom_time() # Ensure custom input is applied if fresh 
            self.is_running = True
            self.start_button.config(text="Pause", bootstyle="warning")
            self.time_entry.config(state="disabled")  # Disable Entry while running
            self.countdown()

    def pause_timer(self):
        """Pauses the timer."""
        self.is_running = False
        self.start_button.config(text="Start", bootstyle=self.accent_style)
        self.time_entry.config(state="normal")  # Re-enable Entry when paused
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def reset_timer(self):
        """Resets the timer to its default duration."""
        self.pause_timer()
        self.apply_custom_time()  # Reset to the current Spinbox value
        self.remaining_seconds = self.default_minutes * 60
        self.timer_label.config(text=self.format_time(self.remaining_seconds))

    def countdown(self):
        """Handles the countdown logic, updating the display every second."""
        if self.is_running and self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.timer_label.config(text=self.format_time(self.remaining_seconds))
            self.timer_id = self.after(1000, self.countdown)
        elif self.is_running and self.remaining_seconds == 0:
            self.reset_timer()
            self.on_complete_callback()

       
class PomodoroApp:
    """Main application controller managing tabs, dot tracker, sizegrip, and the 4 pomodoro cycle."""

    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.geometry("400x360")
        self.root.minsize(380, 330)
        self.root.resizable(True, True)   

        self.pomodoro_count = 0  # Track completed pomodoros
        self.pomodoro_limit = 4  # Number of pomodoros before a long break

        # Replace self.cycle_label with a header frame + CanvasDotTracker for better visual representation
        header_frame = ttk.Frame(self.root)
        header_frame.pack(pady=(15, 5))

        self.dot_tracker = CanvasDotTracker(header_frame, dot_count=self.pomodoro_limit)
        self.dot_tracker.pack()

        # Initialize the dot tracker
        self.dot_tracker.update_count(self.pomodoro_count)

        # Tab Container (Notebook)
        self.notebook = ttk.Notebook(self.root, bootstyle="dark")
        self.notebook.pack(expand=True, fill="both", padx=15, pady=(5, 0))

        # Create the three customizable tabs with distinct accent colors:
        # "danger" (Red/Coral), "success" (Teal/Green), and "info" (Blue/Indigo).
        # Standard defaults: 30m Pomodoro, 10m Short Break, 45m Long Break
        self.pomo_tab = TimerTab(self.notebook, self, "Pomodoro", 30, "danger", self.handle_pomodoro_complete)
        self.short_break_tab = TimerTab(self.notebook, self, "Short Break", 10, "success", self.handle_break_complete)
        self.long_break_tab = TimerTab(self.notebook, self, "Long Break", 45, "info", self.handle_break_complete)

        self.tabs = [self.pomo_tab, self.short_break_tab, self.long_break_tab]

        self.notebook.add(self.pomo_tab, text="Pomodoro")
        self.notebook.add(self.short_break_tab, text="Short Break")
        self.notebook.add(self.long_break_tab, text="Long Break")

        # Bottom-right Sizegrip for resizing the window
        self.sizegrip = ttk.Sizegrip(self.root, bootstyle="secondary")
        self.sizegrip.pack(side=tk.BOTTOM, anchor=tk.SE, padx=3, pady=3)

    def _get_cycle_text(self):
        """Returns visual dot indicators for the 4-Pomodoro cycle."""
        filled_dot = ["●"] * self.pomodoro_count
        empty_dot = ["○"] * (self.pomodoro_limit - self.pomodoro_count)
        return f"Cycle: {''.join(filled_dot + empty_dot)}"

    def stop_all_timers(self, except_tab=None):
        """Stops all timers in the app except for the specified tab."""
        for tab in self.tabs:
            if tab is not except_tab and tab.is_running:
                tab.pause_timer()
                
    def handle_pomodoro_complete(self):
        """ Increments the pomodoro counter and routes to Short Break or 30m Long Break."""
        self.pomodoro_count += 1
        self.dot_tracker.update_count(self.pomodoro_count)
        self.root.bell()  # Audible alert for completion

        if self.pomodoro_count % self.pomodoro_limit == 0:
            messagebox.showinfo("Pomodoro Complete", "Time for a long break!")
            self.notebook.select(self.long_break_tab)
        else:
            messagebox.showinfo(f"Pomodoro {self.pomodoro_count} complete!", "Time for a short break!")
            self.notebook.select(self.short_break_tab)

    def handle_break_complete(self):
        """ Routes back to the Pomodoro tab after a break finishes."""
        self.root.bell()  # Audible alert for completion
        # Reset counter display after a long break finishes a full set of 4
        if self.pomodoro_count >= self.pomodoro_limit:
            self.pomodoro_count = 0
            self.dot_tracker.update_count(self.pomodoro_count)

        messagebox.showinfo("Break Complete", "Time to get back to work!")
        self.notebook.select(self.pomo_tab)

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")  # Use ttkbootstrap's themed window
    app = PomodoroApp(root)
    root.mainloop()
