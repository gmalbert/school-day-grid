<p align="center">
  <img src="static/images/school-day-grid-logo.png" alt="School Day Grid" width="200">
</p>

# School Day Grid

School Day Grid is a standalone school-day sequence and calendar manager. It owns its schedule locally, supports arbitrary rotating-day patterns, closures and holidays, imports school/district ICS calendars, exposes calendar/API outputs, and can optionally integrate with Home Assistant, MQTT, Google Calendar, Microsoft Outlook, webhooks, and ntfy.

The local SQLite schedule is authoritative. External calendars and Home Assistant are optional inputs/outputs, not dependencies.

## First-run onboarding

A new installation opens a guided setup wizard instead of the legacy five-day configuration screen:

1. Welcome / optional sample calendar.
2. School name, school-year dates, timezone, state, arbitrary-length day sequence, and starting sequence day.
3. Optional state holidays and reviewed district `.ics` import.
4. Schedule preview, validation, optional administrator creation, backup, and finish.

After onboarding, `/` redirects to the profile-based calendar UI. The older root dashboard remains only as a migration compatibility layer.

## Password security

When an administrator account is created, School Day Grid **does not store the password in plaintext**. Passwords are stored as salted `PBKDF2-HMAC-SHA256` hashes using a random salt and 240,000 iterations. Authentication is optional unless `SDG_REQUIRE_LOGIN=true` is configured.

For a public Internet deployment, HTTPS, a persistent `SDG_SESSION_SECRET`, CSRF hardening, and a production authentication review are still required before calling the application production-ready.

## Run locally

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn product_app:app --reload --host 0.0.0.0 --port 8088
```

macOS, Linux, or Windows Git Bash:

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# source .venv/Scripts/activate # Windows Git Bash
python -m pip install -e '.[dev]'
cp .env.example .env
python -m uvicorn product_app:app --reload --host 0.0.0.0 --port 8088
```

Then open `http://localhost:8088`.

## Repository layout

The Python application intentionally uses a flat module layout. Files such as
`product_app.py`, `database.py`, and `schedule.py` live directly in the repository root;
there is no `school_day_grid/` source package.

- `product_app.py` — complete FastAPI application entry point;
- root-level `*.py` files — application modules;
- `templates/` and `static/` — browser UI assets;
- `tests/` — automated tests;
- `docs/` — supporting product and integration documentation;
- `data/` — generated SQLite/runtime data, ignored by Git;
- `.venv/` — optional local Python environment, ignored by Git.

## Docker

```bash
docker compose up -d --build
```

The default installation requires no Home Assistant or MQTT configuration.

## Backup

The profile UI includes two backup/export options:

- **Full SQLite backup** — consistent SQLite backup of all profiles, settings, history, sources, and users.
- **Profile JSON export** — portable export of one calendar profile and its schedule data.

## Product documentation

- [Feature implementation matrix](docs/FEATURE_IMPLEMENTATION_MATRIX.md) — implemented feature map.
- [ICS import guide](docs/ICS_IMPORT_GUIDE.md) — uploaded and subscribed ICS behavior.
- [Optional Home Assistant integration](docs/HOME_ASSISTANT_OPTIONAL_INTEGRATION.md) — optional HA/MQTT integration.
- [Product architecture and distribution](docs/PRODUCT_ARCHITECTURE_AND_DISTRIBUTION.md) — architecture and public-release direction.
- [Migration from schoolCycleDays](docs/MIGRATION_FROM_SCHOOLCYCLEDAYS.md) — history and compatibility boundary.
- [Testing guide](docs/TESTING_GUIDE.md) — standalone-first acceptance and integration testing.

## Identity

```text
Product:      School Day Grid
Domain:       schooldaygrid.com
Python dist:  school-day-grid
Python code:  repository root
Env prefix:   SDG_
```
