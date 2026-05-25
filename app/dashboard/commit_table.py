from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from app.dashboard.ui_models import DashboardRow


class CommitTable(ttk.Frame):
    def __init__(self, master: tk.Misc, on_open_url: Callable[[str], None]) -> None:
        super().__init__(master)
        self._on_open_url = on_open_url
        self._urls_by_id: dict[str, str] = {}

        columns = ("repository", "user", "message", "timestamp", "event")
        self._table = ttk.Treeview(self, columns=columns, show="headings", height=12)

        self._table.heading("repository", text="Repository")
        self._table.heading("user", text="User")
        self._table.heading("message", text="Message")
        self._table.heading("timestamp", text="Timestamp")
        self._table.heading("event", text="Event")

        self._table.column("repository", width=160, anchor="w")
        self._table.column("user", width=110, anchor="w")
        self._table.column("message", width=420, anchor="w")
        self._table.column("timestamp", width=170, anchor="w")
        self._table.column("event", width=120, anchor="w")

        self._table.pack(fill=tk.BOTH, expand=True)
        self._table.tag_configure("latest", background="#1f4f2f", foreground="#f2fff2")

        self._table.bind("<Double-1>", self._on_double_click)

    def set_rows(self, rows: list[DashboardRow]) -> None:
        self._table.delete(*self._table.get_children())
        self._urls_by_id.clear()

        for idx, row in enumerate(rows):
            tags = ("latest",) if idx == 0 else ()
            self._table.insert(
                "",
                "end",
                iid=row.event_id,
                values=(
                    row.repository,
                    row.user,
                    row.message,
                    row.timestamp,
                    row.event_type,
                ),
                tags=tags,
            )
            self._urls_by_id[row.event_id] = row.url

    def _on_double_click(self, _event: tk.Event) -> None:
        selected = self._table.selection()
        if not selected:
            return
        item_id = selected[0]
        url = self._urls_by_id.get(item_id)
        if url:
            self._on_open_url(url)
