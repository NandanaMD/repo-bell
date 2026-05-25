from __future__ import annotations

import logging
import queue
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk

from app.dashboard.commit_table import CommitTable
from app.dashboard.ui_models import DashboardRow

logger = logging.getLogger(__name__)


class DashboardWindow:
    """Tkinter-based lightweight activity dashboard."""

    def __init__(self, icon_file: Path | None = None) -> None:
        self._queue: "queue.Queue[tuple[str, list[DashboardRow] | None]]" = queue.Queue()
        self._thread = None
        self._root: tk.Tk | None = None
        self._table: CommitTable | None = None
        self._icon_file = icon_file

    def show(self, initial_rows: list[DashboardRow]) -> None:
        if self._root is not None:
            self._queue.put(("restore", initial_rows))
            return

        self._root = tk.Tk()
        self._root.title("Repo Bell - Activity Dashboard")
        self._root.geometry("1080x420")
        self._root.configure(bg="#171a1f")
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._apply_icon()

        style = ttk.Style(self._root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Dark.TFrame", background="#171a1f")
        style.configure("Dark.TLabel", background="#171a1f", foreground="#d5dbe3")

        frame = ttk.Frame(self._root, style="Dark.TFrame", padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        legend = ttk.Label(frame, text="● Green = Latest Commit", style="Dark.TLabel")
        legend.pack(anchor="w", pady=(0, 8))

        self._table = CommitTable(frame, on_open_url=self._open_url)
        self._table.pack(fill=tk.BOTH, expand=True)
        self._table.set_rows(initial_rows)

        self._poll_queue()
        self._root.mainloop()

    def update_rows(self, rows: list[DashboardRow]) -> None:
        self._queue.put(("rows", rows))

    def _poll_queue(self) -> None:
        if not self._root or not self._table:
            return

        try:
            while True:
                action, payload = self._queue.get_nowait()
                if action == "rows" and payload is not None:
                    self._table.set_rows(payload)
                elif action == "restore":
                    if payload is not None:
                        self._table.set_rows(payload)
                    self._root.deiconify()
                    self._root.lift()
        except queue.Empty:
            pass

        self._root.after(600, self._poll_queue)

    def _open_url(self, url: str) -> None:
        try:
            webbrowser.open(url)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to open url %s: %s", url, exc)

    def _on_close(self) -> None:
        if self._root:
            self._root.withdraw()

    def _apply_icon(self) -> None:
        if not self._root or self._icon_file is None:
            return
        if not self._icon_file.exists():
            return
        try:
            self._root.iconbitmap(default=str(self._icon_file))
        except tk.TclError as exc:
            logger.warning("Failed to apply dashboard icon: %s", exc)
