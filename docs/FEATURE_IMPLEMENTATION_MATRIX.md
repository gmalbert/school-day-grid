# Feature Implementation Matrix

This file maps the major School Day Grid product features to the implementation that currently supports them.

## Core product

| # | Feature | Implementation |
|---|---|---|
| 1 | Automatic snow/emergency-day shift | `ScheduleService.add_snow_day_and_shift()` stores a profile no-school date and rebuilds the sequence. The sequence advances only on school days. |
| 2 | Dry-run / preview | `ScheduleService.preview()` calculates the full schedule without writing it. `GET /api/v1/profiles/{profile}/preview` exposes it. |
| 3 | Interactive calendar editing | Profile schedule dates are clickable in `templates/profile.html`, loading the selected date into the override editor. |
| 4 | Per-date overrides | `schedule_overrides` stores forced school/no-school dates and optional forced sequence numbers, titles, and notes. |
| 5 | Recurring closure rules | `closure_rules` supports weekday, range, month, and nth-occurrence rules expanded by `ScheduleService._rule_dates()`. |
| 6 | Multiple schools / children | `calendar_profiles` scopes sequence definitions, closures, holidays, schedules, tokens, integrations, and audit history. |
| 7 | Household view | `/household` aggregates Today and Next School Day for every profile. |
| 8 | Public read-only share links | `public_share_token` plus `/share/{token}`; tokens can be rotated. |
| 9 | Private ICS subscriptions | Per-profile `ics_token` plus `/calendar/{slug}.ics?token=...`; token rotation is available. |
| 10 | Google Calendar publishing | Google Calendar REST endpoints in `publisher_routes.py`; OAuth access token is used transiently and not stored. |
| 11 | Diff-based external calendar sync | `PublicationSyncPlanner` hashes stable schedule content and classifies create/update/delete/unchanged operations; provider event IDs are stored in `published_events`. |
| 12 | District calendar URL subscriptions | `external_sources` + `ICSUrlSource`; manual refresh and background refresh loop. |
| 13 | Smart ICS matching | URL sources support configurable include/exclude phrases. Uploaded ICS preserves the original strict `SUMMARY starts with No School` behavior. |
| 14 | Import review screen | Uploaded profile ICS uses a two-step review/confirm flow in `review_routes.py` and `templates/ics_review.html`. |
| 15 | Conflict/validation checks | `ScheduleService.validate()` catches missing/short definitions and invalid/out-of-range overrides. |
| 16 | Change history | `audit_log` records rebuilds, imports, profile changes, integrations, sync, and security operations. |
| 17 | Undo | `snapshots` stores bounded pre-change state; management routes restore profile settings, definitions, closures, and overrides before rebuilding. |
| 18 | Local authentication | Optional administrator setup/sign-in with PBKDF2-HMAC-SHA256 passwords and signed sessions. Enable with `SDG_REQUIRE_LOGIN=true`. |
| 19 | PWA support | `/manifest.webmanifest` and `/service-worker.js`; responsive templates support installable/offline-assisted use. |
| 20 | Notifications | Webhook and ntfy targets, test delivery, and a best-effort daily Tomorrow reminder background loop. |

## Additional implemented capabilities

- Standalone SQLite is authoritative; Home Assistant is never required.
- State holidays can be loaded per profile.
- Arbitrary sequence length is supported; A/B, 3-day, 5-day, 6-day, etc. are not hard-coded.
- External `.ics` upload cleanup expands multi-day events and repairs a trailing missing `END:VEVENT`.
- Google Calendar and Microsoft 365/Outlook publishing use create/update/delete reconciliation.
- Generic webhook calendar and notification adapter interfaces exist in `adapters.py`.
- Optional MQTT Home Assistant Discovery publishes Today, Tomorrow, and Next School Day.
- Optional direct Home Assistant adapter exists for legacy migration/publishing only.
- Versioned REST endpoints are rooted under `/api/v1/`.
- JSON profile export is available at `/api/v1/profiles/{profile}/export`.

## Important productization work before public v1.0

The feature paths exist, but a public Internet-facing release should still harden several areas:

1. Add CSRF protection to state-changing browser forms.
2. Add secure cookie/HTTPS configuration and a persistent `SDG_SESSION_SECRET` requirement when login is enabled.
3. Replace transient pasted Google/Microsoft access tokens with first-class OAuth authorization flows.
4. Add explicit database schema versioning/migrations instead of additive `CREATE TABLE IF NOT EXISTS` only.
5. Add backup/restore UI and migration tests.
6. Add rate limiting/login lockout and password-reset/recovery design.
7. Add richer accessibility testing and keyboard-first interactive calendar controls.
8. Add static application icons before PWA store-like distribution.
9. Add browser/API integration tests in addition to core unit tests.
10. Build signed/tagged multi-architecture container releases.
