# ICS Import Guide

School Day Grid can ingest an arbitrary `.ics` calendar file without Home Assistant or another calendar service.

## Historical behavior preserved

The original `schoolCycleDays` project included `apps/cycleDays/no_school_calendar.py`. Its important rule was:

> Keep a VEVENT when its `SUMMARY` starts with `No School`.

The standalone importer preserves that rule for uploaded files, while making the parser more robust and integrating the results directly into the application's no-school dates.

## Upload workflow

From a profile page:

1. Choose **Upload district .ics**.
2. Select the calendar file.
3. School Day Grid extracts matching `No School...` events.
4. A review page lists the candidate dates with checkboxes.
5. Deselect anything you do not want.
6. Confirm the import.
7. Selected dates are stored as profile no-school dates.
8. The profile schedule is rebuilt automatically.

Nothing is imported before the review/confirm step.

The legacy/default page also retains a direct cleanup/import endpoint for compatibility.

## Matching rules for uploaded files

Matching is case-insensitive but anchored to the beginning of the summary. Examples:

```text
No School
No School - Teacher Workshop
NO SCHOOL - Weather
no school - vacation
```

match.

These do not:

```text
District No School Notice
Reminder: No School Tomorrow
Board Meeting
```

## Multi-day events

ICS all-day `DTEND` values are exclusive. For example:

```text
DTSTART;VALUE=DATE:20261223
DTEND;VALUE=DATE:20261227
SUMMARY:No School - Winter Break
```

produces no-school dates for December 23, 24, 25, and 26.

## Malformed trailing event repair

The original helper repaired a final VEVENT when the source file ended without `END:VEVENT`. School Day Grid retains that behavior. The parser appends a closing event marker before trying to parse the trailing block.

A matching event that still cannot be parsed or does not contain a usable `DTSTART` is skipped instead of aborting the entire calendar import.

## Cleaned ICS output

The cleanup routine can also construct a new valid VCALENDAR that contains only the matching No School events. Its PRODID identifies School Day Grid.

This is useful when you want a sanitized school-closure calendar independent of the internal database.

## URL subscriptions

Profiles can also subscribe to an external ICS URL. URL sources use broader configurable include/exclude terms because many districts use labels other than `No School`, such as:

```text
School Closed
Vacation
Teacher Workday
```

The URL-source defaults can be edited when adding the source. Background refresh runs on `SDG_SOURCE_REFRESH_SECONDS` (six hours by default), and a manual refresh is also available.

URL refreshes record a content hash and audit events. If source content changes, matching dates are incorporated and the local schedule is rebuilt.

## Limits

Browser uploads are currently capped at 5 MB.

## Tests

The test suite covers:

- keeping only matching events;
- case-insensitive matching;
- rejecting a phrase that contains but does not start with `No School`;
- multi-day expansion;
- trailing missing `END:VEVENT` repair.

Run:

```bash
pytest -q tests/test_ics_import.py
```
