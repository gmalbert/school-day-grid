# Testing Guide

School Day Grid should be validated first as a completely standalone application. Home Assistant, MQTT, Google, Outlook, and notification services are optional layers tested only after the core works.

## Automated tests

From the repository root:

```bash
python -m compileall *.py tests
python -m pytest -q
python -m ruff check --select E4,E9,F *.py tests
```

These commands reflect the flat module layout: application modules are root-level `*.py`
files, not files in a `school_day_grid/` package. CI also runs the suite on supported Python
versions.

## Core manual acceptance test

1. Start with no HA/MQTT variables configured.
2. Run the full product app:

```bash
python -m uvicorn product_app:app --reload --host 0.0.0.0 --port 8088
```

3. Open `http://localhost:8088`.
4. Configure a short school-year range.
5. Define an A/B or Day 1–5 sequence.
6. Rebuild and confirm only weekdays advance the sequence.
7. Add a no-school date and confirm the following school day receives the sequence value that would have occurred on the closure.
8. Refresh the browser/restart the process and confirm SQLite state persists.

## Multi-profile test

1. Open `/household`.
2. Create a second profile with a different sequence length.
3. Add a closure to only one profile.
4. Confirm the other profile is unchanged.
5. Verify Today and Next School Day cards independently.

## Override test

1. Click a schedule date in a profile.
2. Force it to No School and rebuild.
3. Force another date to a particular sequence number.
4. Confirm the sequence resumes correctly afterward.
5. Remove the override and verify the schedule returns to generated behavior.

## Recurring rule test

Create a short date range and add a recurring Friday closure. Confirm each Friday is blocked and sequence advancement skips those dates.

## ICS upload test

Use an ICS file containing both `No School` and unrelated events. Confirm:

- the review screen contains only matching No School candidates;
- candidate dates can be deselected;
- only confirmed dates are imported;
- multi-day events expand correctly;
- unrelated events are ignored.

Also test a final matching VEVENT missing `END:VEVENT`; the parser should repair the block.

## ICS URL source test

1. Add an external ICS URL with include/exclude terms.
2. Run a manual refresh.
3. Verify matching dates appear as no-school dates.
4. Confirm `last_checked`/hash behavior through subsequent refreshes.
5. Pause the source and verify background refresh ignores it.
6. Remove the source.

## Sharing/ICS security test

1. Open the read-only share URL and confirm there are no editing controls.
2. Rotate the share token and confirm the old URL stops resolving.
3. Open the private ICS feed with the correct token.
4. Confirm a missing/incorrect token returns an authorization error.
5. Rotate the ICS token and confirm the old URL no longer works.

## Audit and Undo

1. Add/remove a closure or override.
2. Verify audit history records the operation.
3. Use Undo.
4. Confirm prior profile settings/state are restored and schedule rebuilt.

## Local authentication

With:

```dotenv
SDG_REQUIRE_LOGIN=true
SDG_SESSION_SECRET=<long-random-value>
```

restart the app, create the first administrator, log out/in, and confirm protected pages redirect anonymous users to `/login`. Read-only share and tokenized calendar routes should remain available according to their own access controls.

## PWA

Verify:

```text
/manifest.webmanifest
/service-worker.js
```

load successfully and the service worker registers in browser developer tools. Offline behavior is currently best-effort cached GET behavior, not a promise that all schedule-management operations work offline.

## Optional integrations

### MQTT

Configure a test broker. Publish manually/rebuild and verify Home Assistant Discovery creates Today, Tomorrow, and Next School Day sensors. Then stop the broker and verify the standalone application still rebuilds and serves pages.

### Home Assistant

Use a non-production HA instance/calendar first. Verify legacy Helper import separately from optional calendar publication. The standalone database must remain correct if HA becomes unavailable.

### Google/Outlook

Use disposable calendars. First inspect the publication plan. Verify initial sync creates events, unchanged sync performs no writes, changed local rows are patched, and removed local rows delete the mapped external event.

### Notifications

Configure a test webhook/ntfy target, send a test notification, and verify the daily Tomorrow delivery is deduplicated by date/target.

## Docker

```bash
docker compose up -d --build
docker compose logs -f school-day-grid
```

Verify data persists in `./data` after container recreation.

## Release gate

Before calling a build ready for broader distribution:

- `compileall` succeeds;
- all unit tests pass;
- standalone manual acceptance passes with integrations disabled;
- Docker starts from a clean checkout;
- profile/sharing/import workflows are tested;
- no secrets are committed;
- optional provider tests are performed only against disposable/test resources.
