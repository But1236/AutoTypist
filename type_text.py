import ctypes
import math
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

from pynput import keyboard, mouse


class TypeTextApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AutoTypist")
        dpi_scale = max(0.75, self.root.winfo_fpixels("1i") / 96)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(
            round(360 * dpi_scale),
            max(round(300 * dpi_scale), screen_width - round(40 * dpi_scale)),
        )
        height = min(
            round(235 * dpi_scale),
            max(round(200 * dpi_scale), screen_height - round(50 * dpi_scale)),
        )
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(
            min(round(300 * dpi_scale), width),
            min(round(200 * dpi_scale), height),
        )
        self.root.configure(bg="#ffffff")

        self.delay_var = tk.StringVar(value="5")
        self.interval_var = tk.StringVar(value="0.05")
        self.status_var = tk.StringVar(value="天才打字手准备就绪：填写内容后点击“开始输入”。")
        self.pending_text: str | None = None
        self.pending_interval = 0.05
        self.keyboard = keyboard.Controller()
        self.mouse = mouse.Controller()
        self.typing_index = 0
        self.deadline = 0.0
        self.after_id: str | None = None
        self.failsafe_after_id: str | None = None

        self._build_ui()
        self.root.update_idletasks()
        width = max(width, self.root.winfo_reqwidth())
        height = max(height, self.root.winfo_reqheight())
        self.root.geometry(f"{width}x{height}")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#ffffff")
        style.configure(
            "TLabel",
            background="#ffffff",
            foreground="#111111",
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "TSpinbox",
            fieldbackground="#ffffff",
            foreground="#111111",
            background="#e5e5e5",
            arrowcolor="#111111",
            bordercolor="#777777",
            lightcolor="#ffffff",
            darkcolor="#999999",
            font=("Microsoft YaHei UI", 9),
        )
        style.map(
            "TSpinbox",
            fieldbackground=[("disabled", "#eeeeee"), ("readonly", "#ffffff")],
            foreground=[("disabled", "#666666"), ("readonly", "#111111")],
            background=[("disabled", "#eeeeee")],
        )
        style.configure(
            "Vertical.TScrollbar",
            background="#e5e5e5",
            troughcolor="#f5f5f5",
            arrowcolor="#111111",
            bordercolor="#aaaaaa",
        )

        frame = ttk.Frame(self.root, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        status_frame = tk.Frame(frame, bg="#eeeeee", padx=7, pady=5)
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg="#eeeeee",
            fg="#111111",
            font=("Microsoft YaHei UI", 10, "bold"),
            anchor="w",
        )
        self.status_label.pack(fill=tk.X)

        ttk.Label(frame, text="输入内容").grid(row=1, column=0, sticky="w")
        text_frame = ttk.Frame(frame)
        text_frame.grid(row=2, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.text_box = tk.Text(
            text_frame,
            wrap=tk.WORD,
            undo=True,
            width=30,
            height=3,
            font=("Microsoft YaHei UI", 10),
            padx=8,
            pady=6,
            bg="#ffffff",
            fg="#111111",
            insertbackground="#111111",
            selectbackground="#bdbdbd",
            selectforeground="#111111",
            highlightbackground="#aaaaaa",
            highlightcolor="#111111",
            highlightthickness=1,
            relief=tk.FLAT,
        )
        self.text_box.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.text_box.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_box.configure(yscrollcommand=scrollbar.set)

        controls = ttk.Frame(frame)
        controls.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        settings = ttk.Frame(controls)
        settings.pack(side=tk.LEFT, fill=tk.Y)
        self.delay_up_button, self.delay_down_button = self._add_stepper(
            settings, "等待（秒）", self.delay_var, 1, 0, 86400
        )
        self.interval_up_button, self.interval_down_button = self._add_stepper(
            settings, "间隔（秒）", self.interval_var, 0.01, 0.01, 10
        )

        actions = ttk.Frame(controls)
        actions.pack(side=tk.RIGHT, anchor="e")
        self.start_button = tk.Button(
            actions,
            text="开始输入",
            command=self.start,
            width=8,
            height=1,
            bg="#111111",
            fg="#ffffff",
            activebackground="#444444",
            activeforeground="#ffffff",
            disabledforeground="#888888",
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=0,
            font=("Microsoft YaHei UI", 10, "bold"),
            cursor="hand2",
        )
        self.start_button.pack(side=tk.LEFT, padx=(4, 3))
        self.cancel_button = tk.Button(
            actions,
            text="停止输入",
            command=self.cancel,
            width=8,
            height=1,
            bg="#ffffff",
            fg="#111111",
            activebackground="#e5e5e5",
            activeforeground="#111111",
            disabledforeground="#888888",
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=0,
            font=("Microsoft YaHei UI", 10, "bold"),
            cursor="hand2",
            state=tk.DISABLED,
        )
        self.cancel_button.pack(side=tk.LEFT)

        ttk.Label(
            frame,
            text="倒计时结束前切换到目标窗口；鼠标移到左上角可紧急停止。",
        ).grid(row=4, column=0, sticky="w", pady=(3, 0))

    def _add_stepper(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        step: float,
        minimum: float,
        maximum: float,
    ) -> tuple[tk.Button, tk.Button]:
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, anchor="w", pady=2)
        ttk.Label(row, text=label, width=10).pack(side=tk.LEFT)
        value = tk.Label(
            row,
            textvariable=variable,
            width=7,
            bg="#ffffff",
            fg="#111111",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Microsoft YaHei UI", 9),
            padx=4,
            pady=4,
        )
        value.pack(side=tk.LEFT, padx=(0, 3))

        button_options = {
            "width": 2,
            "height": 0,
            "bg": "#ffffff",
            "fg": "#111111",
            "activebackground": "#e5e5e5",
            "activeforeground": "#111111",
            "disabledforeground": "#888888",
            "relief": tk.SOLID,
            "borderwidth": 1,
            "highlightthickness": 0,
            "font": ("Segoe UI Symbol", 5, "bold"),
            "cursor": "hand2",
            "padx": 0,
            "pady": 0,
        }
        step_buttons = ttk.Frame(row)
        step_buttons.pack(side=tk.LEFT)
        up_button = tk.Button(
            step_buttons,
            text="▲",
            command=lambda: self._adjust_value(
                variable, step, minimum, maximum
            ),
            **button_options,
        )
        up_button.pack(side=tk.TOP, fill=tk.X)
        down_button = tk.Button(
            step_buttons,
            text="▼",
            command=lambda: self._adjust_value(
                variable, -step, minimum, maximum
            ),
            **button_options,
        )
        down_button.pack(side=tk.TOP, fill=tk.X)
        return up_button, down_button

    @staticmethod
    def _adjust_value(
        variable: tk.StringVar, step: float, minimum: float, maximum: float
    ) -> None:
        step = float(step)
        current = float(variable.get())
        value = min(maximum, max(minimum, current + step))
        precision = 0 if step.is_integer() else 2
        variable.set(f"{value:.{precision}f}" if precision else str(int(value)))

    def start(self) -> None:
        if self.after_id is not None:
            return

        content = self.text_box.get("1.0", "end-1c")
        if not content:
            messagebox.showerror("无法开始", "打字员还不知道要打的内容。", parent=self.root)
            return

        try:
            delay = float(self.delay_var.get().strip())
        except ValueError:
            messagebox.showerror(
                "等待时间无效", "请输入 0 到 86400 之间的秒数。", parent=self.root
            )
            return

        if not math.isfinite(delay) or not 0 <= delay <= 86400:
            messagebox.showerror(
                "等待时间无效", "请输入 0 到 86400 之间的秒数。", parent=self.root
            )
            return

        try:
            interval = float(self.interval_var.get().strip())
        except ValueError:
            messagebox.showerror(
                "打字间隔无效", "请输入 0.01 到 10 秒之间的数值。", parent=self.root
            )
            return

        if not math.isfinite(interval) or not 0.01 <= interval <= 10:
            messagebox.showerror(
                "打字间隔无效", "请输入 0.01 到 10 秒之间的数值。", parent=self.root
            )
            return

        self.pending_text = content
        self.pending_interval = interval
        self.typing_index = 0
        self.deadline = time.monotonic() + delay
        self.start_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.text_box.configure(state=tk.DISABLED)
        self._set_adjustment_buttons_state(tk.DISABLED)
        self._set_status("准备倒计时：请切换到目标输入框。", "info")
        self._schedule_failsafe_check()
        self._update_countdown()

    def _update_countdown(self) -> None:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            self._set_status("打字员疯狂敲键盘中：将鼠标移到左上角可立即停止。", "warning")
            self._type_next_char()
            return

        self._set_status(
            f"倒计时：{math.ceil(remaining)} 秒后开始动手。请切换到目标输入框；"
            "移到左上角可停止。",
            "info",
        )
        self.after_id = self.root.after(
            min(100, max(1, int(remaining * 1000))), self._update_countdown
        )

    def _type_next_char(self) -> None:
        self.after_id = None
        content = self.pending_text
        if content is None:
            self._set_idle()
            return

        if self.typing_index >= len(content):
            self._set_status("天才打字员打字完成！", "success")
            self.pending_text = None
            self._set_idle()
            return

        try:
            self.keyboard.type(content[self.typing_index])
        except (keyboard.Controller.InvalidCharacterException, OSError) as exc:
            self._set_status("天才打字员打字失败。", "error")
            messagebox.showerror("天才打字员打字失败", str(exc), parent=self.root)
            self.pending_text = None
            self._set_idle()
            return

        self.typing_index += 1
        if self.typing_index == len(content):
            self._set_status("天才打字员打字完成！", "success")
            self.pending_text = None
            self._set_idle()
            return

        self._set_status(
            f"打字员正在输入：{self.typing_index}/{len(content)} 个字符。"
            "移到屏幕左上角可停止。",
            "warning",
        )
        self.after_id = self.root.after(
            max(10, round(self.pending_interval * 1000)), self._type_next_char
        )

    def _schedule_failsafe_check(self) -> None:
        self.failsafe_after_id = self.root.after(30, self._check_failsafe)

    def _check_failsafe(self) -> None:
        self.failsafe_after_id = None
        if self.pending_text is None:
            return

        try:
            x, y = self.mouse.position
        except OSError as exc:
            self._set_status("无法检测鼠标位置，输入已停止。", "error")
            messagebox.showerror("打字员没看到你的鼠标位置，打字停止", str(exc), parent=self.root)
            self.pending_text = None
            self._set_idle()
            return

        if x <= 2 and y <= 2:
            was_typing = self.typing_index > 0
            self.cancel(failsafe=True, was_typing=was_typing)
            return

        self._schedule_failsafe_check()

    def cancel(self, failsafe: bool = False, was_typing: bool | None = None) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if was_typing is None:
            was_typing = self.typing_index > 0
        self.pending_text = None
        if failsafe:
            message = (
                "紧急停止：鼠标移到左上角，已停止输入（部分内容可能已输入）。"
                if was_typing
                else "紧急停止：鼠标移到左上角，输入已取消。"
            )
            self._set_status(message, "error")
        else:
            self._set_status(
                "已停止（部分内容可能已输入）。" if was_typing else "已取消。",
                "info",
            )
        self._set_idle()

    def _set_idle(self) -> None:
        if self.failsafe_after_id is not None:
            self.root.after_cancel(self.failsafe_after_id)
            self.failsafe_after_id = None
        self.start_button.configure(state=tk.NORMAL)
        self.cancel_button.configure(state=tk.DISABLED)
        self.text_box.configure(state=tk.NORMAL)
        self._set_adjustment_buttons_state(tk.NORMAL)

    def _set_adjustment_buttons_state(self, state: str) -> None:
        for button in (
            self.delay_up_button,
            self.delay_down_button,
            self.interval_up_button,
            self.interval_down_button,
        ):
            button.configure(state=state)

    def _set_status(self, message: str, kind: str) -> None:
        colors = {
            "info": ("#eeeeee", "#111111"),
            "warning": ("#dddddd", "#111111"),
            "success": ("#f5f5f5", "#111111"),
            "error": ("#cccccc", "#000000"),
        }
        background, foreground = colors[kind]
        self.status_var.set(message)
        self.status_label.configure(bg=background, fg=foreground)
        self.status_label.master.configure(bg=background)

    def close(self) -> None:
        self.cancel()
        self.root.destroy()


def main() -> None:
    enable_dpi_awareness()
    root = tk.Tk()
    TypeTextApp(root)
    root.mainloop()


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    try:
        set_dpi_context = user32.SetProcessDpiAwarenessContext
    except AttributeError:
        set_dpi_context = None

    if set_dpi_context is not None:
        set_dpi_context.argtypes = [ctypes.c_void_p]
        set_dpi_context.restype = ctypes.c_bool
        if set_dpi_context(ctypes.c_void_p(-4)):
            return

    try:
        shcore = ctypes.WinDLL("shcore", use_last_error=True)
        set_dpi_awareness = shcore.SetProcessDpiAwareness
    except (AttributeError, OSError):
        set_dpi_awareness = None

    if set_dpi_awareness is not None:
        set_dpi_awareness.argtypes = [ctypes.c_int]
        set_dpi_awareness.restype = ctypes.c_long
        if set_dpi_awareness(2) == 0:
            return

    user32.SetProcessDPIAware()


if __name__ == "__main__":
    main()
