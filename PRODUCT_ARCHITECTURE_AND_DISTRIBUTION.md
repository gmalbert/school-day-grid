# Product Architecture and Distribution

## Product identity

**School Day Grid** is a standalone, self-hosted school-day rotation and calendar manager. The domain acquired for the project is `schooldaygrid.com`.

The application is intentionally independent of Home Assistant. Its local SQLite database and scheduling engine are authoritative; integrations are optional inputs/outputs.

## Architecture

```text
Browser / PWA
      |
      v
School Day Grid (FastAPI)
├── profile & household UI
├── schedule/sequence engine
├── SQLite persistence
├── ICS upload + review
├── ICS URL subscriptions
├── REST API
├── private/public sharing
├── notifications
└── integration adapters
      |
      +-- ICS clients
      +-- MQTT / Home Assistant
      +-- Google Calendar
      +-- Microsoft 365 / Outlook
      +-- webhooks / ntfy
```

## Data ownership

The authoritative objects are stored locally:

- `calendar_profiles`
- `cycle_definitions` (historical internal table name; represents arbitrary day sequences)
- `profile_non_school_days`
- `profile_holidays`
- `schedule_overrides`
- `closure_rules`
- `profile_schedule`
- `external_sources`
- `published_events`
- `audit_log`
- `snapshots`
- `users`
- `notification_targets`

External calendars are projections or import sources. They do not become the source of truth.

## Profile model

Each profile represents a school/child/calendar and owns:

- name and slug;
- timezone;
- school-year start/end;
- starting sequence day;
- state holiday configuration;
- arbitrary ordered day labels;
- no-school dates and holidays;
- one-off overrides;
- recurring closure rules;
- external calendar sources;
- generated schedule;
- share and ICS tokens;
- audit/snapshot history;
- publication mappings and notification targets.

A household view combines multiple profiles without merging their schedules.

## Scheduling behavior

The engine walks the configured school year in date order. Weekends and blocked days do not advance the sequence. Valid school days consume the next sequence label. Therefore adding a snow/emergency closure automatically shifts every later school day without manual restart-day arithmetic.

Overrides can force a date to no-school or force a particular school sequence number. Recurring rules are expanded into blocked dates during preview/rebuild.

`preview()` is side-effect free. `rebuild_profile()` persists the generated rows.

## Outputs

### REST API

The public integration namespace is `/api/v1/`. Existing endpoints include health, today/tomorrow/next-school-day, schedule ranges, profiles, preview, validation, and profile export.

### ICS

- Default compatibility feed: `/calendar.ics`
- Private profile feed: `/calendar/{slug}.ics?token=...`

### Sharing

Read-only browser views use rotatable random tokens.

### MQTT

Optional Home Assistant Discovery publishes Today, Tomorrow, and Next School Day states. MQTT is not required.

### Google and Microsoft

Provider sync uses a content-hash planner and stored provider event IDs to classify create/update/delete/unchanged operations. Current UI accepts access tokens transiently; first-class OAuth is a pre-v1.0 requirement.

## Deployment

### Python

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn school_day_grid.product_app:app --host 0.0.0.0 --port 8088
```

### Docker

```bash
docker compose up -d --build
```

The container persists `/data/school_day_grid.sqlite3` through the local `./data` volume.

## Configuration

All environment settings use the `SDG_` prefix in the new repository. Home Assistant and MQTT values are blank by default.

When login is enabled, set a strong persistent `SDG_SESSION_SECRET`. Do not rely on the process-generated fallback secret for a production multi-restart deployment because sessions will be invalidated on restart.

## Distribution roadmap

### v0.x / development

- Continue UI/UX refinement.
- Add database migration framework and schema version table.
- Expand automated tests around browser routes/background loops/integrations.
- Add backup and restore.
- Add a first-run onboarding flow.
- Add application icons and accessibility refinement.

### Pre-v1 security gate

Before recommending Internet exposure:

- CSRF protection for all form writes;
- secure/HTTPS-only session cookies behind TLS;
- rate limiting and login throttling;
- password reset/recovery strategy;
- secrets storage review;
- OAuth authorization-code flows for Google/Microsoft/Home Assistant where appropriate;
- dependency and container vulnerability scanning;
- explicit threat-model review of public share and ICS tokens.

### Release engineering

Recommended public-release pipeline:

1. GitHub Actions on Python 3.12/3.13.
2. `compileall`, `ruff`, and `pytest` on every PR/push.
3. Tagged semantic-version releases.
4. Multi-architecture container image published to GHCR.
5. Release notes generated from merged changes.
6. Database migration tests from previous supported release.
7. Optional SBOM/container signing once the project is broadly distributed.

## Repository split

This repository should remain distinct from `gmalbert/schoolCycleDays`.

`schoolCycleDays` is the historical Home Assistant/AppDaemon project and migration source. `school-day-grid` is the standalone product. Legacy HA entity names/markers may remain in a compatibility module specifically so existing users can migrate, but new product development belongs here.
