# Repo Bell

Repo Bell is a lightweight Windows tray app that monitors GitHub repositories and sends native desktop notifications.

It is designed to be simple for daily use: install, add repos, and start getting alerts.

---

## 2-Minute Quick Start (Recommended)

This path uses **polling mode** and requires no webhook setup.

1. Install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the app:

```powershell
python -m app.main
```

3. In tray menu, click `Open Settings`.
4. Add one or more repositories (`owner`, `repo`, optional `token`).
5. Keep `mode = polling`, then click `Save Settings`.
6. Repo Bell reloads config and starts monitoring.

That is all you need for normal usage.

## Features

- Windows tray app with low-overhead background monitoring
- Native toast notifications for push, merge, and release events
- Polling mode (default and recommended)
- Webhook mode (advanced, lower latency)
- In-app settings editor (no manual JSON editing required)
- Multi-repository support with per-repo enable toggle
- Built-in activity dashboard (latest 10 events)
- Green highlight for the most recent event
- Shared app icon (`assets/icon.ico`) across tray, windows, and toasts
- Duplicate prevention persisted in `data/state.json`
- Rotating logs in `data/logs/`
- Optional startup with Windows

---

## Which Mode Should I Choose?

- `polling`: easiest setup, works immediately, no inbound network requirements
- `webhook`: faster event delivery, requires webhook endpoint setup

For most users, start with `polling`.

---

## Running Locally

```powershell
python -m app.main
```

The app starts in tray and begins monitoring based on current config.

Script mode also works:

```powershell
python app/main.py
```

---

## Tray Menu

- `Start Monitoring`
- `Stop Monitoring`
- `Reload Config`
- `Open Settings`
- `Open Activity Dashboard`
- `Open Logs Folder`
- `Open Config Folder`
- `Enable/Disable Notifications`
- `Exit`

---

## In-App Configuration

Use `Open Settings` from tray to manage everything inside the app:

- mode (`polling` or `webhook`)
- poll interval
- repositories (`owner`, `repo`, `token`, `enabled`)
- webhook settings (`enabled`, `port`, `secret`, fallback)
- notify users filter
- startup with Windows
- log level
- sound notification toggle

When you click `Save Settings`, Repo Bell writes `data/config.json` and reloads services automatically.

### Config File

Repo Bell still uses `data/config.json` as source of truth.

```json
{
  "mode": "polling",
  "poll_interval": 60,
  "webhook": {
    "enabled": true,
    "port": 8080,
    "secret": "",
    "polling_fallback": false
  },
  "repositories": [
    {
      "owner": "microsoft",
      "repo": "vscode",
      "token": "",
      "enabled": true
    }
  ],
  "notify_users": [],
  "sound_notification": true,
  "start_with_windows": false,
  "log_level": "INFO"
}
```

---

## Activity Dashboard

Open via tray: `Open Activity Dashboard`

- Shows latest 10 events (newest first)
- Green row highlights the latest event
- Legend: `Green = Latest Commit`
- Columns: repository, user, message, timestamp, event
- Double-click row opens event URL in browser
- Closing dashboard hides the window (tray app keeps running)

---

## Advanced: Webhook Mode Setup

Webhook mode is optional.

### 1) Enable webhook mode

In settings or `data/config.json`:

- `mode = webhook`
- `webhook.enabled = true`
- `webhook.port = <port>`
- `webhook.secret = <shared-secret>`

### 2) Configure GitHub webhook

In repository settings:

1. Go to `Settings -> Webhooks -> Add webhook`
2. Payload URL: `http://<your-host>:8080/webhook`
3. Content type: `application/json`
4. Secret: same as `webhook.secret`
5. Events: Pushes, Pull requests, Releases
6. Save

### 3) Local development note

If running locally, expose port with a tunnel (example: ngrok) and use the tunnel URL in GitHub webhook settings.

---

## Architecture

Core modules:

- `app/main.py`: composition root and lifecycle orchestration
- `app/tray/tray_app.py`: tray UI and actions
- `app/tray/settings_window.py`: in-app settings editor
- `app/dashboard/*`: dashboard UI
- `app/github/client.py`: GitHub API calls
- `app/github/polling_monitor.py`: polling worker thread
- `app/webhook/server.py`: webhook listener
- `app/storage/state_store.py`: thread-safe persistence
- `app/storage/activity_feed.py`: rolling in-memory event cache

Event flow:

1. Polling/webhook receives activity
2. Duplicate filter checks persisted event IDs
3. Event is persisted and published to activity feed
4. Toast notification is sent
5. Dashboard refreshes automatically

---

## Packaging (PyInstaller)

Build command:

```powershell
pyinstaller --onefile --noconsole --icon=assets/icon.ico --add-data "assets;assets" app/main.py
```

Or run:

```powershell
build.bat
```

Output: `dist\RepoBell.exe`

---

## Windows Installer (Inno Setup)

Repo Bell includes an Inno Setup script at `installer/RepoBell.iss`.

Installer includes:

- Terms and Conditions page (`installer/terms_and_conditions.txt`)
- Task checkbox: `Create desktop icon`
- Task checkbox: `Start Repo Bell with Windows`

### Build installer

1. Build executable first (`dist\RepoBell.exe`)
2. Open `installer/RepoBell.iss` in Inno Setup Compiler
3. Click Compile

Output installer: `installer/output/RepoBellSetup.exe`

---

## Startup With Windows

When enabled, Repo Bell writes a user-level startup entry to:

`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

No admin privileges are required.

---

## Troubleshooting

Logs: `data/logs/repobell.log`

- No notifications: check tray toggle + Windows notification permissions
- No updates in polling mode: verify repo and token permissions
- Webhook `401`: secret mismatch
- Config save/reload errors: verify settings values (port, intervals, repo fields)
- Rate limits: configure a token for each repository where needed

---

## Tests

```powershell
python -m unittest discover -s tests
```

---

## Contributing

1. Fork the repository
2. Create a branch
3. Add or update tests
4. Run test suite
5. Open a pull request

---

## AI-Assisted Development Disclosure

This project was developed with the assistance of AI tools for code generation, architecture planning, and development acceleration. All code was reviewed, modified, tested, and curated for production use.

---

## License

MIT License. See `LICENSE`.
