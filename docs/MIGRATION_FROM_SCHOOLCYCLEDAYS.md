# Migration from schoolCycleDays

School Day Grid was split from the standalone product work developed during the modernization of `gmalbert/schoolCycleDays`.

## What moved

The new repository contains the standalone product only:

- FastAPI application and standalone web calendar;
- SQLite persistence and arbitrary day-sequence engine;
- multi-profile/household support;
- closures, holidays, overrides, audit, and undo;
- ICS upload cleanup/review and ICS URL subscriptions;
- REST/ICS/PWA outputs;
- Google/Outlook/webhook/ntfy/MQTT integrations;
- optional legacy Home Assistant adapter;
- tests and product documentation.

## What did not move

The following remain in the historical repository and are not part of School Day Grid:

- AppDaemon application files;
- Home Assistant custom-component prototype;
- HACS metadata for the historical integration;
- old Home Assistant dashboard examples;
- direct Local Calendar `.ics` manipulation code.

## Compatibility intentionally retained

Some identifiers still contain the historical `school_cycle_days` name. These are compatibility contracts, not the new brand:

- the legacy Home Assistant generated-event marker `[school_cycle_days]`;
- historical Home Assistant Helper entity IDs;
- selected internal database field/table names such as `cycle_day` and `cycle_definitions`;
- Google private metadata used to recognize already-published legacy events.

Changing those during the initial repo split could break migration or orphan events. New public naming, module entry points, environment variables, Docker naming, MQTT entity identity, PWA metadata, and ICS identifiers use School Day Grid.

## New repository identity

```text
GitHub:       gmalbert/school-day-grid
Product:      School Day Grid
Domain:       schooldaygrid.com
Python dist:  school-day-grid
Python code:  repository root
Env prefix:   SDG_
Database:     school_day_grid.sqlite3
```

## Migrating a development checkout

A fresh checkout should be preferred rather than trying to repoint the old working tree:

```bash
git clone https://github.com/gmalbert/school-day-grid.git
cd school-day-grid
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# source .venv/Scripts/activate # Windows Git Bash
python -m pip install -e '.[dev]'
cp .env.example .env
python -m uvicorn product_app:app --reload --host 0.0.0.0 --port 8088
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and copy the environment
file with `Copy-Item .env.example .env`.

## Migrating data

During early development, start with a fresh database unless you specifically need existing state. For legacy Home Assistant data, configure the optional HA adapter and use the legacy Helper import path. It copies useful settings/non-school dates/holidays without making Home Assistant authoritative.

A formal database import/migration command should be added before a public v1.0 release. Until then, do not treat raw SQLite file copying between historical development builds as a stable public migration API.

## Repository ownership rule

All future standalone-product features should be developed in `school-day-grid`. The historical repo should receive only maintenance or migration changes that specifically concern its AppDaemon/Home Assistant implementation.
