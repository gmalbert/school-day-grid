# School Day Grid

School Day Grid is a standalone school-day rotation and calendar manager. It owns its schedule locally, supports arbitrary rotating-day patterns, closures and holidays, imports school/district ICS calendars, exposes calendar/API outputs, and can optionally integrate with Home Assistant, MQTT, Google Calendar, Microsoft Outlook, webhooks, and ntfy.

This repository was split from the standalone product work originally developed in `gmalbert/schoolCycleDays`. The original AppDaemon/Home Assistant project remains separate.

## Run locally

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -e '.[dev]'
cp .env.example .env
uvicorn school_day_grid.product_app:app --reload --host 0.0.0.0 --port 8088
```

Then open `http://localhost:8088`.

See the included architecture, feature, ICS-import, distribution, and optional Home Assistant integration documentation for details.
