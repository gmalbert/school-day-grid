# Technical reference

> For the product overview, screenshots, and the guided first-run experience, return to the [main README](../README.md).

This page is for developers, self-hosters, and people integrating School Day Grid with other systems.

## Application layout

The application uses a deliberately flat Python module layout:

- `product_app.py` is the FastAPI application entry point.
- Root-level `*.py` files contain application modules.
- `templates/` and `static/` contain the browser interface.
- `tests/` contains automated tests.
- `data/` holds generated SQLite and runtime data and is ignored by Git.

There is no `school_day_grid/` source package.

## Data and integrations

The local SQLite schedule is the source of truth. External calendars and Home Assistant are optional inputs or outputs; they are not required for the app to run.

The profile interface supports:

- full SQLite backups containing profiles, settings, history, sources, and users;
- portable JSON export for a single calendar profile;
- optional ICS imports and subscriptions;
- optional Home Assistant, MQTT, Google Calendar, Microsoft Outlook, webhook, and ntfy connections.

## Security notes

If an administrator account is created, its password is stored as a salted PBKDF2-HMAC-SHA256 hash with a random salt and 240,000 iterations. Authentication remains optional unless `SDG_REQUIRE_LOGIN=true` is configured.

Before exposing an installation to the public Internet, use HTTPS, configure a persistent `SDG_SESSION_SECRET`, enable appropriate CSRF protections, and perform a production authentication review.

## Environment and identity

```text
Product:      School Day Grid
Domain:       schooldaygrid.com
Python dist:  school-day-grid
Python code:  repository root
Env prefix:   SDG_
```

Copy `.env.example` to `.env` before configuring optional integration settings. See the [installation guide](GETTING_STARTED.md) for the commands that start the application.

## Detailed developer documentation

- [Feature implementation matrix](FEATURE_IMPLEMENTATION_MATRIX.md)
- [ICS import guide](ICS_IMPORT_GUIDE.md)
- [Optional Home Assistant integration](HOME_ASSISTANT_OPTIONAL_INTEGRATION.md)
- [Product architecture and distribution](PRODUCT_ARCHITECTURE_AND_DISTRIBUTION.md)
- [Migration from schoolCycleDays](MIGRATION_FROM_SCHOOLCYCLEDAYS.md)
- [Testing guide](TESTING_GUIDE.md)
