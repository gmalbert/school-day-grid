# School Day Grid

School Day Grid is a standalone school-day sequence and calendar manager. It owns its schedule locally, supports arbitrary rotating-day patterns, closures and holidays, imports school/district ICS calendars, exposes calendar/API outputs, and can optionally integrate with Home Assistant, MQTT, Google Calendar, Microsoft Outlook, webhooks, and ntfy.

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

## Docker

```bash
docker compose up -d --build
```

The default installation requires no Home Assistant or MQTT configuration.

## Product documentation

- `FEATURE_IMPLEMENTATION_MATRIX.md` — implemented feature map.
- `ICS_IMPORT_GUIDE.md` — uploaded and subscribed ICS behavior.
- `HOME_ASSISTANT_OPTIONAL_INTEGRATION.md` — optional HA/MQTT integration.
- `PRODUCT_ARCHITECTURE_AND_DISTRIBUTION.md` — architecture and public-release direction.
- `docs/MIGRATION_FROM_SCHOOLCYCLEDAYS.md` — history and compatibility boundary.
- `docs/TESTING_GUIDE.md` — standalone-first acceptance and integration testing.

## Identity

```text
Product:      School Day Grid
Domain:       schooldaygrid.com
Python dist:  school-day-grid
Python pkg:   school_day_grid
Env prefix:   SDG_
```

The local SQLite schedule is authoritative. External calendars and Home Assistant are optional inputs/outputs, not dependencies.
