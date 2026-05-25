from __future__ import annotations

import logging
import queue
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable
from urllib.parse import urlparse

from app.config.models import AppConfig, RepositoryConfig, WebhookConfig

logger = logging.getLogger(__name__)

SaveCallback = Callable[[AppConfig], None]


class SettingsWindow:
    """Lightweight in-app configuration editor."""

    def __init__(self, on_save: SaveCallback, icon_file: Path | None = None) -> None:
        self._on_save = on_save
        self._queue: "queue.Queue[tuple[str, AppConfig | None]]" = queue.Queue()
        self._icon_file = icon_file

        self._root: tk.Tk | None = None
        self._repo_table: ttk.Treeview | None = None

        self._mode_var: tk.StringVar | None = None
        self._poll_interval_var: tk.StringVar | None = None
        self._notify_users_var: tk.StringVar | None = None
        self._log_level_var: tk.StringVar | None = None
        self._sound_var: tk.BooleanVar | None = None
        self._startup_var: tk.BooleanVar | None = None

        self._webhook_enabled_var: tk.BooleanVar | None = None
        self._webhook_port_var: tk.StringVar | None = None
        self._webhook_secret_var: tk.StringVar | None = None
        self._webhook_fallback_var: tk.BooleanVar | None = None

        self._repo_owner_var: tk.StringVar | None = None
        self._repo_name_var: tk.StringVar | None = None
        self._repo_token_var: tk.StringVar | None = None
        self._repo_enabled_var: tk.BooleanVar | None = None

        self._repositories: list[RepositoryConfig] = []

    def show(self, config: AppConfig) -> None:
        if self._root is not None:
            self._queue.put(("populate", config))
            return

        self._root = tk.Tk()
        self._root.title("Repo Bell - Settings")
        self._root.geometry("980x620")
        self._root.configure(bg="#171a1f")
        self._root.protocol("WM_DELETE_WINDOW", self._hide)
        self._apply_icon()
        self._init_variables()

        style = ttk.Style(self._root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        container = ttk.Frame(self._root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        self._build_general_section(container)
        self._build_webhook_section(container)
        self._build_repository_section(container)
        self._build_actions(container)

        self._populate(config)
        self._poll_queue()
        self._root.mainloop()

    def _init_variables(self) -> None:
        self._mode_var = tk.StringVar(value="polling")
        self._poll_interval_var = tk.StringVar(value="60")
        self._notify_users_var = tk.StringVar(value="")
        self._log_level_var = tk.StringVar(value="INFO")
        self._sound_var = tk.BooleanVar(value=True)
        self._startup_var = tk.BooleanVar(value=False)

        self._webhook_enabled_var = tk.BooleanVar(value=True)
        self._webhook_port_var = tk.StringVar(value="8080")
        self._webhook_secret_var = tk.StringVar(value="")
        self._webhook_fallback_var = tk.BooleanVar(value=False)

        self._repo_owner_var = tk.StringVar(value="")
        self._repo_name_var = tk.StringVar(value="")
        self._repo_token_var = tk.StringVar(value="")
        self._repo_enabled_var = tk.BooleanVar(value=True)

    def _sv(self, value: tk.StringVar | None) -> tk.StringVar:
        if value is None:
            raise RuntimeError("Settings variables are not initialized")
        return value

    def _bv(self, value: tk.BooleanVar | None) -> tk.BooleanVar:
        if value is None:
            raise RuntimeError("Settings variables are not initialized")
        return value

    def _build_general_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="General")
        frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(frame, text="Mode").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        mode = ttk.Combobox(frame, state="readonly", textvariable=self._sv(self._mode_var), values=["polling", "webhook"], width=12)
        mode.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Poll Interval (sec)").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self._sv(self._poll_interval_var), width=10).grid(row=0, column=3, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Log Level").grid(row=0, column=4, padx=6, pady=6, sticky="w")
        log_level = ttk.Combobox(
            frame,
            state="readonly",
            textvariable=self._sv(self._log_level_var),
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            width=10,
        )
        log_level.grid(row=0, column=5, padx=6, pady=6, sticky="w")

        ttk.Checkbutton(frame, text="Sound Notification", variable=self._bv(self._sound_var)).grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="w")
        ttk.Checkbutton(frame, text="Start With Windows", variable=self._bv(self._startup_var)).grid(row=1, column=2, columnspan=2, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Notify Users (comma-separated)").grid(row=1, column=4, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self._sv(self._notify_users_var), width=30).grid(row=1, column=5, padx=6, pady=6, sticky="w")

    def _build_webhook_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Webhook")
        frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Checkbutton(frame, text="Webhook Enabled", variable=self._bv(self._webhook_enabled_var)).grid(row=0, column=0, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Port").grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self._sv(self._webhook_port_var), width=10).grid(row=0, column=2, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Secret").grid(row=0, column=3, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self._sv(self._webhook_secret_var), width=28, show="*").grid(row=0, column=4, padx=6, pady=6, sticky="w")

        ttk.Checkbutton(frame, text="Enable Polling Fallback", variable=self._bv(self._webhook_fallback_var)).grid(row=0, column=5, padx=6, pady=6, sticky="w")

    def _build_repository_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Repositories")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        columns = ("owner", "repo", "token", "enabled")
        self._repo_table = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self._repo_table.heading("owner", text="Owner")
        self._repo_table.heading("repo", text="Repository")
        self._repo_table.heading("token", text="Token")
        self._repo_table.heading("enabled", text="Enabled")

        self._repo_table.column("owner", width=170, anchor="w")
        self._repo_table.column("repo", width=190, anchor="w")
        self._repo_table.column("token", width=270, anchor="w")
        self._repo_table.column("enabled", width=80, anchor="center")
        self._repo_table.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self._repo_table.bind("<<TreeviewSelect>>", self._on_repo_selected)

        editor = ttk.Frame(frame)
        editor.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(editor, text="Owner").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        ttk.Entry(editor, textvariable=self._sv(self._repo_owner_var), width=18).grid(row=0, column=1, padx=4, pady=4, sticky="w")

        ttk.Label(editor, text="Repo").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        ttk.Entry(editor, textvariable=self._sv(self._repo_name_var), width=18).grid(row=0, column=3, padx=4, pady=4, sticky="w")

        ttk.Label(editor, text="Token").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        ttk.Entry(editor, textvariable=self._sv(self._repo_token_var), width=28, show="*").grid(row=0, column=5, padx=4, pady=4, sticky="w")

        ttk.Checkbutton(editor, text="Enabled", variable=self._bv(self._repo_enabled_var)).grid(row=0, column=6, padx=4, pady=4, sticky="w")

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, padx=6, pady=(0, 6))
        ttk.Button(buttons, text="Add", command=self._add_repo).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Update Selected", command=self._update_selected_repo).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Remove Selected", command=self._remove_selected_repo).pack(side=tk.LEFT, padx=4)

    def _build_actions(self, parent: ttk.Frame) -> None:
        actions = ttk.Frame(parent)
        actions.pack(fill=tk.X)

        ttk.Button(actions, text="Save Settings", command=self._save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(actions, text="Close", command=self._hide).pack(side=tk.RIGHT, padx=4)

    def _populate(self, config: AppConfig) -> None:
        self._sv(self._mode_var).set(config.mode)
        self._sv(self._poll_interval_var).set(str(config.poll_interval))
        self._sv(self._notify_users_var).set(", ".join(config.notify_users))
        self._sv(self._log_level_var).set(config.log_level)
        self._bv(self._sound_var).set(config.sound_notification)
        self._bv(self._startup_var).set(config.start_with_windows)

        self._bv(self._webhook_enabled_var).set(config.webhook.enabled)
        self._sv(self._webhook_port_var).set(str(config.webhook.port))
        self._sv(self._webhook_secret_var).set(config.webhook.secret)
        self._bv(self._webhook_fallback_var).set(config.webhook.polling_fallback)

        self._repositories = list(config.repositories)
        self._refresh_repo_table()

    def _poll_queue(self) -> None:
        if not self._root:
            return
        try:
            while True:
                action, config = self._queue.get_nowait()
                if action == "populate" and config is not None:
                    self._populate(config)
                    self._root.deiconify()
                    self._root.lift()
        except queue.Empty:
            pass

        self._root.after(500, self._poll_queue)

    def _refresh_repo_table(self) -> None:
        if not self._repo_table:
            return

        self._repo_table.delete(*self._repo_table.get_children())
        for idx, item in enumerate(self._repositories):
            masked = "" if not item.token else f"***{item.token[-4:]}"
            self._repo_table.insert(
                "",
                "end",
                iid=str(idx),
                values=(item.owner, item.repo, masked, "Yes" if item.enabled else "No"),
            )

    def _add_repo(self) -> None:
        repo = self._read_repo_editor()
        if repo is None:
            return
        self._repositories.append(repo)
        self._refresh_repo_table()
        self._clear_repo_editor()

    def _update_selected_repo(self) -> None:
        if not self._repo_table:
            return

        selected = self._repo_table.selection()
        if not selected:
            messagebox.showwarning("Repo Bell", "Select a repository row to update.")
            return

        repo = self._read_repo_editor()
        if repo is None:
            return
        index = int(selected[0])
        self._repositories[index] = repo
        self._refresh_repo_table()

    def _remove_selected_repo(self) -> None:
        if not self._repo_table:
            return

        selected = self._repo_table.selection()
        if not selected:
            messagebox.showwarning("Repo Bell", "Select a repository row to remove.")
            return

        index = int(selected[0])
        del self._repositories[index]
        self._refresh_repo_table()

    def _on_repo_selected(self, _event: tk.Event) -> None:
        if not self._repo_table:
            return
        selected = self._repo_table.selection()
        if not selected:
            return

        index = int(selected[0])
        repo = self._repositories[index]
        self._sv(self._repo_owner_var).set(repo.owner)
        self._sv(self._repo_name_var).set(repo.repo)
        self._sv(self._repo_token_var).set(repo.token)
        self._bv(self._repo_enabled_var).set(repo.enabled)

    def _read_repo_editor(self) -> RepositoryConfig | None:
        owner = self._sv(self._repo_owner_var).get().strip()
        repo = self._sv(self._repo_name_var).get().strip()
        token = self._sv(self._repo_token_var).get().strip()
        enabled = self._bv(self._repo_enabled_var).get()

        owner, repo = self._normalize_repo_input(owner, repo)

        if not owner or not repo:
            messagebox.showerror("Repo Bell", "Repository owner and name are required.")
            return None

        return RepositoryConfig(owner=owner, repo=repo, token=token, enabled=enabled)

    def _normalize_repo_input(self, owner: str, repo: str) -> tuple[str, str]:
        repo_value = repo.strip()

        if repo_value.startswith("http://") or repo_value.startswith("https://"):
            parsed = urlparse(repo_value)
            host = parsed.netloc.lower()
            if "github.com" not in host:
                messagebox.showerror("Repo Bell", "Only GitHub repository URLs are supported.")
                return "", ""

            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) < 2:
                messagebox.showerror("Repo Bell", "Invalid GitHub repository URL.")
                return "", ""

            parsed_owner = parts[0]
            parsed_repo = parts[1].removesuffix(".git")
            return parsed_owner, parsed_repo

        if "/" in repo_value and not owner:
            parts = [part.strip() for part in repo_value.split("/", maxsplit=1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                return parts[0], parts[1]

        if repo_value.endswith(".git"):
            repo_value = repo_value[: -len(".git")]

        return owner, repo_value

    def _clear_repo_editor(self) -> None:
        self._sv(self._repo_owner_var).set("")
        self._sv(self._repo_name_var).set("")
        self._sv(self._repo_token_var).set("")
        self._bv(self._repo_enabled_var).set(True)

    def _save(self) -> None:
        if not self._repositories:
            messagebox.showerror("Repo Bell", "At least one repository is required.")
            return

        try:
            poll_interval = int(self._sv(self._poll_interval_var).get().strip())
            webhook_port = int(self._sv(self._webhook_port_var).get().strip())
        except ValueError:
            messagebox.showerror("Repo Bell", "Poll interval and webhook port must be numbers.")
            return

        if poll_interval < 10:
            messagebox.showerror("Repo Bell", "Poll interval must be 10 or greater.")
            return

        if not (1 <= webhook_port <= 65535):
            messagebox.showerror("Repo Bell", "Webhook port must be between 1 and 65535.")
            return

        notify_users = [
            item.strip()
            for item in self._sv(self._notify_users_var).get().split(",")
            if item.strip()
        ]

        config = AppConfig(
            mode=self._sv(self._mode_var).get(),
            poll_interval=poll_interval,
            webhook=WebhookConfig(
                enabled=self._bv(self._webhook_enabled_var).get(),
                port=webhook_port,
                secret=self._sv(self._webhook_secret_var).get(),
                polling_fallback=self._bv(self._webhook_fallback_var).get(),
            ),
            repositories=list(self._repositories),
            notify_users=notify_users,
            sound_notification=self._bv(self._sound_var).get(),
            start_with_windows=self._bv(self._startup_var).get(),
            log_level=self._sv(self._log_level_var).get(),
        )

        try:
            self._on_save(config)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save settings: %s", exc)
            messagebox.showerror("Repo Bell", f"Failed to save settings: {exc}")
            return

        messagebox.showinfo("Repo Bell", "Settings saved successfully.")

    def _hide(self) -> None:
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
            logger.warning("Failed to apply settings icon: %s", exc)
