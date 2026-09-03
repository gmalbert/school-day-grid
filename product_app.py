"""Final distributable School Day Grid app composition."""
from __future__ import annotations

import asyncio
import secrets
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from main import app, database, runtime, schedule, templates
from management_routes import build_management_router
from notifications import notification_loop
from onboarding_routes import build_onboarding_router, onboarding_complete
from product_routes import build_product_router, subscription_refresh_loop
from publisher_routes import build_publisher_router
from review_routes import build_review_router
from security_routes import build_security_router

app.title = "School Day Grid"
app.version = "0.5.0"
app.add_middleware(
    SessionMiddleware,
    secret_key=runtime.session_secret or secrets.token_urlsafe(32),
    same_site="lax",
    https_only=False,
)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "static"),
    name="static",
)

app.include_router(build_onboarding_router(database, schedule, templates))
app.include_router(build_management_router(database, schedule))
app.include_router(build_product_router(database, schedule, templates))
app.include_router(build_review_router(database, schedule, templates))
app.include_router(build_publisher_router(database, schedule))
app.include_router(build_security_router(database))

PUBLIC_PREFIXES = (
    "/favicon.ico",
    "/login",
    "/setup-admin",
    "/onboarding",
    "/share/",
    "/calendar/",
    "/api/v1/health",
    "/manifest.webmanifest",
    "/service-worker.js",
    "/static/",
)
PRE_SETUP_ONLY_PATHS = {"/backup/database"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> RedirectResponse:
    """Offer a conventional favicon URL alongside the scalable SVG icon."""
    return RedirectResponse("/static/icons/icon-192.svg", status_code=307)


@app.middleware("http")
async def product_navigation_and_auth(request: Request, call_next):
    path = request.url.path
    setup_complete = onboarding_complete(database)
    public_path = path.startswith(PUBLIC_PREFIXES)

    if not setup_complete and not public_path and path not in PRE_SETUP_ONLY_PATHS:
        return RedirectResponse("/onboarding", 303)

    if (
        setup_complete
        and runtime.require_login
        and not public_path
        and not request.session.get("user_id")
    ):
        return RedirectResponse("/login", 303)

    if path == "/":
        if not setup_complete:
            return RedirectResponse("/onboarding", 303)
        profiles = database.profiles()
        if profiles:
            return RedirectResponse(f"/profile/{profiles[0]['id']}", 303)
        return RedirectResponse("/onboarding", 303)

    return await call_next(request)


_refresh_task: asyncio.Task | None = None
_notification_task: asyncio.Task | None = None


@app.on_event("startup")
async def product_startup():
    global _refresh_task, _notification_task
    _refresh_task = asyncio.create_task(
        subscription_refresh_loop(database, schedule, runtime.source_refresh_seconds)
    )
    _notification_task = asyncio.create_task(notification_loop(database, schedule))


@app.on_event("shutdown")
async def product_shutdown():
    for task in (_refresh_task, _notification_task):
        if task:
            task.cancel()
