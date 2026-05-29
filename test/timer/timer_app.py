import math
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import winsound
except ImportError:  # pragma: no cover - non-Windows fallback
    winsound = None


BG = "#f6f1e8"
PANEL = "#fffaf0"
INK = "#2f2b25"
MUTED = "#776f63"
ACCENT = "#2f7d75"
ACCENT_DARK = "#1d5e57"
WARNING = "#c75b43"
RING_BG = "#e6ded1"


class TimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("桌面倒计时 / 计时器小助手")
        self.geometry("520x680")
        self.minsize(430, 620)
        self.configure(bg=BG)

        self.mode = tk.StringVar(value="countdown")
        self.always_on_top = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="准备开始")

        self.countdown_running = False
        self.countdown_duration = 5 * 60
        self.countdown_remaining = self.countdown_duration
        self.countdown_end_at = None
        self.countdown_job = None
        self.alarm_job = None
        self.alarm_flash = False

        self.stopwatch_running = False
        self.stopwatch_elapsed = 0.0
        self.stopwatch_started_at = None
        self.stopwatch_job = None
        self.lap_count = 0

        self._build_ui()
        self._bind_keys()
        self._refresh_display()

    def _build_ui(self):
        root = ttk.Frame(self, padding=22)
        root.pack(fill="both", expand=True)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Title.TLabel", background=BG, foreground=INK, font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Hint.TLabel", background=BG, foreground=MUTED, font=("Microsoft YaHei UI", 10))
        style.configure("Status.TLabel", background=BG, foreground=ACCENT_DARK, font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(12, 8))
        style.configure("Primary.TButton", foreground="white", background=ACCENT, font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", ACCENT_DARK), ("pressed", ACCENT_DARK)])
        style.configure("Danger.TButton", foreground="white", background=WARNING, font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Danger.TButton", background=[("active", "#a84431"), ("pressed", "#a84431")])
        style.configure("TCheckbutton", background=BG, foreground=INK, font=("Microsoft YaHei UI", 10))

        header = ttk.Frame(root)
        header.pack(fill="x")
        ttk.Label(header, text="桌面计时器", style="Title.TLabel").pack(side="left")
        ttk.Checkbutton(
            header,
            text="置顶",
            variable=self.always_on_top,
            command=self._toggle_topmost,
        ).pack(side="right")
        ttk.Label(root, text="倒计时、正计时、提醒与暂停恢复都在这里完成。", style="Hint.TLabel").pack(
            anchor="w", pady=(4, 16)
        )

        mode_bar = ttk.Frame(root)
        mode_bar.pack(fill="x", pady=(0, 14))
        self.countdown_mode_button = ttk.Button(
            mode_bar,
            text="倒计时",
            command=lambda: self._switch_mode("countdown"),
            style="Primary.TButton",
        )
        self.stopwatch_mode_button = ttk.Button(
            mode_bar,
            text="计时器",
            command=lambda: self._switch_mode("stopwatch"),
        )
        self.countdown_mode_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.stopwatch_mode_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

        dial_frame = ttk.Frame(root, style="Panel.TFrame", padding=18)
        dial_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(dial_frame, width=360, height=300, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        ttk.Label(root, textvariable=self.status, style="Status.TLabel").pack(pady=(14, 10))

        self.countdown_panel = ttk.Frame(root)
        self.countdown_panel.pack(fill="x")
        self._build_countdown_panel(self.countdown_panel)

        self.stopwatch_panel = ttk.Frame(root)
        self._build_stopwatch_panel(self.stopwatch_panel)

        footer = ttk.Label(
            root,
            text="快捷键：空格开始/暂停，R 重置，Esc 关闭提醒",
            style="Hint.TLabel",
        )
        footer.pack(anchor="center", pady=(14, 0))

    def _build_countdown_panel(self, parent):
        inputs = ttk.Frame(parent)
        inputs.pack(fill="x", pady=(0, 10))
        self.hour_var = tk.IntVar(value=0)
        self.minute_var = tk.IntVar(value=5)
        self.second_var = tk.IntVar(value=0)
        self._time_input(inputs, "时", self.hour_var, 0, 23).pack(side="left", expand=True, fill="x", padx=(0, 6))
        self._time_input(inputs, "分", self.minute_var, 0, 59).pack(side="left", expand=True, fill="x", padx=6)
        self._time_input(inputs, "秒", self.second_var, 0, 59).pack(side="left", expand=True, fill="x", padx=(6, 0))

        presets = ttk.Frame(parent)
        presets.pack(fill="x", pady=(0, 10))
        for label, seconds in [("5 分钟", 300), ("10 分钟", 600), ("25 分钟", 1500), ("45 分钟", 2700)]:
            ttk.Button(presets, text=label, command=lambda value=seconds: self._set_countdown_seconds(value)).pack(
                side="left", expand=True, fill="x", padx=3
            )

        controls = ttk.Frame(parent)
        controls.pack(fill="x")
        self.countdown_start_button = ttk.Button(
            controls,
            text="开始",
            command=self._toggle_countdown,
            style="Primary.TButton",
        )
        self.countdown_start_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ttk.Button(controls, text="重置", command=self._reset_countdown).pack(
            side="left", expand=True, fill="x", padx=6
        )
        ttk.Button(controls, text="停止提醒", command=self._stop_alarm, style="Danger.TButton").pack(
            side="left", expand=True, fill="x", padx=(6, 0)
        )

    def _build_stopwatch_panel(self, parent):
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=(0, 10))
        self.stopwatch_start_button = ttk.Button(
            controls,
            text="开始",
            command=self._toggle_stopwatch,
            style="Primary.TButton",
        )
        self.stopwatch_start_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ttk.Button(controls, text="计次", command=self._record_lap).pack(side="left", expand=True, fill="x", padx=6)
        ttk.Button(controls, text="重置", command=self._reset_stopwatch).pack(
            side="left", expand=True, fill="x", padx=(6, 0)
        )

        lap_frame = ttk.Frame(parent, style="Panel.TFrame")
        lap_frame.pack(fill="both", expand=False)
        self.lap_list = tk.Listbox(
            lap_frame,
            height=6,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=RING_BG,
            bg=PANEL,
            fg=INK,
            font=("Consolas", 12),
            activestyle="none",
        )
        self.lap_list.pack(fill="both", expand=True)

    def _time_input(self, parent, label, variable, from_, to):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text=label, style="Hint.TLabel").pack(anchor="center")
        spin = ttk.Spinbox(
            frame,
            from_=from_,
            to=to,
            textvariable=variable,
            width=4,
            justify="center",
            command=self._load_countdown_from_inputs,
            font=("Consolas", 15, "bold"),
        )
        spin.pack(fill="x", pady=(3, 0))
        spin.bind("<KeyRelease>", lambda _event: self._load_countdown_from_inputs())
        spin.bind("<FocusOut>", lambda _event: self._load_countdown_from_inputs())
        return frame

    def _bind_keys(self):
        self.bind("<space>", lambda _event: self._toggle_active_mode())
        self.bind("<Key-r>", lambda _event: self._reset_active_mode())
        self.bind("<Key-R>", lambda _event: self._reset_active_mode())
        self.bind("<Escape>", lambda _event: self._stop_alarm())

    def _switch_mode(self, mode):
        self.mode.set(mode)
        if mode == "countdown":
            self.stopwatch_panel.pack_forget()
            self.countdown_panel.pack(fill="x")
            self.countdown_mode_button.configure(style="Primary.TButton")
            self.stopwatch_mode_button.configure(style="TButton")
            self.status.set("倒计时模式")
        else:
            self.countdown_panel.pack_forget()
            self.stopwatch_panel.pack(fill="x")
            self.countdown_mode_button.configure(style="TButton")
            self.stopwatch_mode_button.configure(style="Primary.TButton")
            self.status.set("计时器模式")
        self._refresh_display()

    def _toggle_topmost(self):
        self.attributes("-topmost", bool(self.always_on_top.get()))

    def _toggle_active_mode(self):
        if self.mode.get() == "countdown":
            self._toggle_countdown()
        else:
            self._toggle_stopwatch()

    def _reset_active_mode(self):
        if self.mode.get() == "countdown":
            self._reset_countdown()
        else:
            self._reset_stopwatch()

    def _set_countdown_seconds(self, seconds):
        if self.countdown_running:
            return
        self.hour_var.set(seconds // 3600)
        self.minute_var.set((seconds % 3600) // 60)
        self.second_var.set(seconds % 60)
        self._load_countdown_from_inputs()
        self.status.set(f"已设置 {self._format_seconds(seconds)}")

    def _load_countdown_from_inputs(self):
        if self.countdown_running:
            return
        hours = self._safe_int(self.hour_var.get(), 0, 23)
        minutes = self._safe_int(self.minute_var.get(), 0, 59)
        seconds = self._safe_int(self.second_var.get(), 0, 59)
        self.hour_var.set(hours)
        self.minute_var.set(minutes)
        self.second_var.set(seconds)
        total = hours * 3600 + minutes * 60 + seconds
        self.countdown_duration = max(total, 1)
        self.countdown_remaining = self.countdown_duration
        self._refresh_display()

    def _safe_int(self, value, low, high):
        try:
            parsed = int(value)
        except (TypeError, ValueError, tk.TclError):
            parsed = low
        return max(low, min(high, parsed))

    def _toggle_countdown(self):
        self._stop_alarm()
        if self.countdown_running:
            self._pause_countdown()
        else:
            if self.countdown_remaining <= 0:
                self._load_countdown_from_inputs()
            self._start_countdown()

    def _start_countdown(self):
        self.countdown_running = True
        self.countdown_end_at = time.monotonic() + self.countdown_remaining
        self.countdown_start_button.configure(text="暂停")
        self.status.set("倒计时进行中")
        self._tick_countdown()

    def _pause_countdown(self):
        self.countdown_running = False
        if self.countdown_job:
            self.after_cancel(self.countdown_job)
            self.countdown_job = None
        if self.countdown_end_at is not None:
            self.countdown_remaining = max(0.0, self.countdown_end_at - time.monotonic())
        self.countdown_start_button.configure(text="继续")
        self.status.set("已暂停")
        self._refresh_display()

    def _reset_countdown(self):
        self._stop_alarm()
        self.countdown_running = False
        if self.countdown_job:
            self.after_cancel(self.countdown_job)
            self.countdown_job = None
        self._load_countdown_from_inputs()
        self.countdown_start_button.configure(text="开始")
        self.status.set("已重置倒计时")

    def _tick_countdown(self):
        if not self.countdown_running or self.countdown_end_at is None:
            return
        self.countdown_remaining = max(0.0, self.countdown_end_at - time.monotonic())
        self._refresh_display()
        if self.countdown_remaining <= 0:
            self.countdown_running = False
            self.countdown_start_button.configure(text="开始")
            self.status.set("时间到")
            self._play_alarm()
            messagebox.showinfo("倒计时结束", "时间到！")
            return
        self.countdown_job = self.after(150, self._tick_countdown)

    def _toggle_stopwatch(self):
        if self.stopwatch_running:
            self._pause_stopwatch()
        else:
            self._start_stopwatch()

    def _start_stopwatch(self):
        self.stopwatch_running = True
        self.stopwatch_started_at = time.monotonic() - self.stopwatch_elapsed
        self.stopwatch_start_button.configure(text="暂停")
        self.status.set("计时器运行中")
        self._tick_stopwatch()

    def _pause_stopwatch(self):
        self.stopwatch_running = False
        if self.stopwatch_job:
            self.after_cancel(self.stopwatch_job)
            self.stopwatch_job = None
        if self.stopwatch_started_at is not None:
            self.stopwatch_elapsed = time.monotonic() - self.stopwatch_started_at
        self.stopwatch_start_button.configure(text="继续")
        self.status.set("已暂停")
        self._refresh_display()

    def _reset_stopwatch(self):
        self.stopwatch_running = False
        if self.stopwatch_job:
            self.after_cancel(self.stopwatch_job)
            self.stopwatch_job = None
        self.stopwatch_elapsed = 0.0
        self.stopwatch_started_at = None
        self.lap_count = 0
        self.lap_list.delete(0, "end")
        self.stopwatch_start_button.configure(text="开始")
        self.status.set("已重置计时器")
        self._refresh_display()

    def _tick_stopwatch(self):
        if not self.stopwatch_running or self.stopwatch_started_at is None:
            return
        self.stopwatch_elapsed = time.monotonic() - self.stopwatch_started_at
        self._refresh_display()
        self.stopwatch_job = self.after(60, self._tick_stopwatch)

    def _record_lap(self):
        if self.mode.get() != "stopwatch":
            return
        self.lap_count += 1
        self.lap_list.insert(0, f"#{self.lap_count:02d}  {self._format_precise(self.stopwatch_elapsed)}")
        self.status.set("已记录计次")

    def _play_alarm(self):
        self._stop_alarm()
        self.alarm_flash = False
        self._alarm_pulse()

    def _alarm_pulse(self):
        self.alarm_flash = not self.alarm_flash
        if winsound is not None:
            winsound.Beep(880 if self.alarm_flash else 660, 160)
        else:
            self.bell()
        self._refresh_display()
        self.alarm_job = self.after(550, self._alarm_pulse)

    def _stop_alarm(self):
        if self.alarm_job:
            self.after_cancel(self.alarm_job)
            self.alarm_job = None
        self.alarm_flash = False
        self._refresh_display()

    def _refresh_display(self):
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 320)
        height = max(self.canvas.winfo_height(), 260)
        size = min(width, height) - 34
        cx = width / 2
        cy = height / 2 + 4
        radius = size / 2

        self._draw_alarm_shell(cx, cy, radius)

        if self.mode.get() == "countdown":
            progress = self._countdown_progress()
            text = self._format_seconds(math.ceil(self.countdown_remaining))
            subtitle = "倒计时"
            color = WARNING if self.alarm_job and self.alarm_flash else ACCENT
        else:
            progress = self._stopwatch_progress()
            text = self._format_precise(self.stopwatch_elapsed)
            subtitle = "计时器"
            color = ACCENT

        bbox = (cx - radius + 22, cy - radius + 22, cx + radius - 22, cy + radius - 22)
        self.canvas.create_arc(bbox, start=90, extent=-360, style="arc", outline=RING_BG, width=14)
        self.canvas.create_arc(bbox, start=90, extent=-360 * progress, style="arc", outline=color, width=14)
        self.canvas.create_text(cx, cy - 8, text=text, fill=INK, font=("Consolas", 35, "bold"))
        self.canvas.create_text(cx, cy + 40, text=subtitle, fill=MUTED, font=("Microsoft YaHei UI", 13, "bold"))

    def _draw_alarm_shell(self, cx, cy, radius):
        bell_r = radius * 0.23
        foot_y = cy + radius * 0.88
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#fff7e8", outline="#d6c8b4", width=4)
        self.canvas.create_oval(
            cx - radius * 0.78,
            cy - radius * 1.25,
            cx - radius * 0.28,
            cy - radius * 0.78,
            fill="#f1c36d",
            outline="#c99439",
            width=3,
        )
        self.canvas.create_oval(
            cx + radius * 0.28,
            cy - radius * 1.25,
            cx + radius * 0.78,
            cy - radius * 0.78,
            fill="#f1c36d",
            outline="#c99439",
            width=3,
        )
        self.canvas.create_line(cx - radius * 0.48, foot_y, cx - radius * 0.68, foot_y + bell_r, fill="#8c7354", width=5)
        self.canvas.create_line(cx + radius * 0.48, foot_y, cx + radius * 0.68, foot_y + bell_r, fill="#8c7354", width=5)
        self.canvas.create_line(cx - 18, cy - radius * 1.03, cx + 18, cy - radius * 1.03, fill="#8c7354", width=5)

    def _countdown_progress(self):
        if self.countdown_duration <= 0:
            return 0.0
        return 1.0 - min(1.0, max(0.0, self.countdown_remaining / self.countdown_duration))

    def _stopwatch_progress(self):
        return (self.stopwatch_elapsed % 60) / 60

    def _format_seconds(self, value):
        value = max(0, int(value))
        hours = value // 3600
        minutes = (value % 3600) // 60
        seconds = value % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _format_precise(self, value):
        value = max(0.0, float(value))
        hours = int(value // 3600)
        minutes = int((value % 3600) // 60)
        seconds = int(value % 60)
        centiseconds = int((value - int(value)) * 100)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def main():
    app = TimerApp()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
