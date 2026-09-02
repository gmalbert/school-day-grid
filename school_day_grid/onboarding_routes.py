"""First-run onboarding, PWA metadata, and backup routes."""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
import tempfile
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import holidays
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.background import BackgroundTask
from starlette.templating import Jinja2Templates

from .database import Database
from .ics_import import clean_no_school_calendar
from .schedule import ScheduleService

MAX_ICS_BYTES = 5 * 1024 * 1024


def _password_hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 240_000
    )
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def _has_users(db: Database) -> bool:
    with db._connect() as connection:
        return bool(connection.execute("SELECT 1 FROM users LIMIT 1").fetchone())


def onboarding_complete(db: Database) -> bool:
    return bool(db.get_settings().get("onboarding_completed", False))


def _primary_profile(db: Database) -> dict:
    profiles = db.profiles()
    if profiles:
        return profiles[0]
    profile_id = db.create_profile("School Calendar", "school")
    profile = db.profile(profile_id)
    if not profile:
        raise RuntimeError("Unable to create initial profile")
    return profile


def _validate_profile(
    start: str,
    end: str,
    timezone: str,
    labels: list[str],
    starting_day: int,
) -> tuple[date, date]:
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError as exc:
        raise HTTPException(400, "Use valid school-year dates") from exc
    if end_date < start_date:
        raise HTTPException(400, "School-year end must be on or after the start")
    if not labels:
        raise HTTPException(400, "Add at least one day-sequence label")
    if starting_day < 1 or starting_day > len(labels):
        raise HTTPException(400, "Starting day must exist in the configured sequence")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(400, "Use a valid IANA timezone such as America/New_York") from exc
    return start_date, end_date


def build_onboarding_router(
    db: Database, schedule: ScheduleService, templates: Jinja2Templates
) -> APIRouter:
    router = APIRouter()

    def redirect(step: int, message: str = "") -> RedirectResponse:
        suffix = f"?step={step}"
        if message:
            from urllib.parse import quote
            suffix += f"&message={quote(message)}"
        return RedirectResponse(f"/onboarding{suffix}", 303)

    @router.get("/onboarding", response_class=HTMLResponse)
    async def onboarding(request: Request, step: int = 1, message: str = ""):
        profile = _primary_profile(db)
        preview_rows = []
        warnings = []
        if profile["school_year_start"] and profile["school_year_end"]:
            try:
                preview_rows, _ = schedule.preview(profile["id"])
                preview_rows = preview_rows[:35]
                warnings = schedule.validate(profile["id"])
            except ValueError:
                preview_rows = []
        return templates.TemplateResponse(
            request,
            "onboarding.html",
            {
                "step": max(1, min(step, 4)),
                "profile": profile,
                "cycles": db.cycles(profile["id"]),
                "preview_rows": preview_rows,
                "warnings": warnings,
                "ics_candidates": request.session.get("onboarding_ics_candidates", []),
                "has_users": _has_users(db),
                "message": message,
            },
        )

    @router.post("/onboarding/profile")
    async def save_profile(
        name: str = Form(...),
        school_year_start: str = Form(...),
        school_year_end: str = Form(...),
        timezone: str = Form("America/New_York"),
        us_state: str = Form("NH"),
        starting_cycle_day: int = Form(1),
        cycle_labels: str = Form(...),
    ):
        labels = [line.strip() for line in cycle_labels.splitlines() if line.strip()]
        _validate_profile(
            school_year_start,
            school_year_end,
            timezone.strip(),
            labels,
            starting_cycle_day,
        )
        if len(us_state.strip()) != 2:
            raise HTTPException(400, "US state must be a two-letter code")
        profile = _primary_profile(db)
        with db._connect() as connection:
            connection.execute(
                "UPDATE calendar_profiles SET name=?,school_year_start=?,school_year_end=?,"
                "timezone=?,us_state=?,starting_cycle_day=? WHERE id=?",
                (
                    name.strip(),
                    school_year_start,
                    school_year_end,
                    timezone.strip(),
                    us_state.strip().upper(),
                    starting_cycle_day,
                    profile["id"],
                ),
            )
        db.set_cycles(profile["id"], labels)
        schedule.rebuild_profile(profile["id"])
        return redirect(3, "Calendar basics saved. Add known days off or continue.")

    @router.post("/onboarding/holidays")
    async def load_holidays():
        profile = _primary_profile(db)
        if not profile["school_year_start"] or not profile["school_year_end"]:
            raise HTTPException(400, "Configure the school year first")
        start = date.fromisoformat(profile["school_year_start"])
        end = date.fromisoformat(profile["school_year_end"])
        values = holidays.US(
            state=profile["us_state"], years=range(start.year, end.year + 1)
        )
        rows = sorted(
            (day.isoformat(), str(name))
            for day, name in values.items()
            if start <= day <= end
        )
        with db._connect() as connection:
            connection.execute(
                "DELETE FROM profile_holidays WHERE profile_id=?", (profile["id"],)
            )
            connection.executemany(
                "INSERT INTO profile_holidays(profile_id,day,name) VALUES(?,?,?)",
                [(profile["id"], day, name) for day, name in rows],
            )
        schedule.rebuild_profile(profile["id"])
        return redirect(3, f"Loaded {len(rows)} state holidays.")

    @router.post("/onboarding/ics-preview")
    async def preview_ics(request: Request, calendar_file: UploadFile = File(...)):
        raw = await calendar_file.read(MAX_ICS_BYTES + 1)
        if len(raw) > MAX_ICS_BYTES:
            raise HTTPException(413, "ICS file is larger than 5 MB")
        result = clean_no_school_calendar(raw)
        candidates = []
        seen: set[str] = set()
        for event in result.events:
            for event_date in event.dates:
                value = event_date.isoformat()
                if value not in seen:
                    candidates.append({"day": value, "summary": event.summary})
                    seen.add(value)
        request.session["onboarding_ics_candidates"] = candidates
        return redirect(3, f"Found {len(candidates)} candidate no-school dates. Review them below.")

    @router.post("/onboarding/ics-import")
    async def import_ics(request: Request, selected_days: list[str] = Form(default=[])):
        profile = _primary_profile(db)
        candidates = {
            item["day"]: item
            for item in request.session.get("onboarding_ics_candidates", [])
        }
        imported = 0
        for day_value in selected_days:
            item = candidates.get(day_value)
            if not item:
                continue
            db.add_profile_non_school(
                profile["id"], day_value, "ics_upload", item["summary"], "onboarding"
            )
            imported += 1
        request.session.pop("onboarding_ics_candidates", None)
        schedule.rebuild_profile(profile["id"])
        return redirect(4, f"Imported {imported} reviewed no-school dates.")

    @router.post("/onboarding/demo")
    async def demo_calendar():
        profile = _primary_profile(db)
        today = date.today()
        academic_year = today.year if today.month >= 7 else today.year - 1
        start = date(academic_year, 9, 1)
        end = date(academic_year + 1, 6, 20)
        labels = ["Art", "Music", "Phys Ed", "Technology", "Library"]
        with db._connect() as connection:
            connection.execute(
                "UPDATE calendar_profiles SET name=?,school_year_start=?,school_year_end=?,"
                "starting_cycle_day=1 WHERE id=?",
                ("Sample School", start.isoformat(), end.isoformat(), profile["id"]),
            )
        db.set_cycles(profile["id"], labels)
        sample_closure = start + timedelta(days=30)
        while sample_closure.weekday() >= 5:
            sample_closure += timedelta(days=1)
        db.add_profile_non_school(
            profile["id"], sample_closure.isoformat(), "demo", "Sample No School Day"
        )
        schedule.rebuild_profile(profile["id"])
        return redirect(4, "Sample calendar created. Review it, then finish or go back and replace it.")

    @router.post("/onboarding/admin")
    async def create_admin(username: str = Form(...), password: str = Form(...)):
        if _has_users(db):
            return redirect(4, "An administrator already exists.")
        if len(password) < 10:
            raise HTTPException(400, "Administrator password must be at least 10 characters")
        with db._connect() as connection:
            connection.execute(
                "INSERT INTO users(username,password_hash,role,created_at) "
                "VALUES(?,?,?,datetime('now'))",
                (username.strip(), _password_hash(password), "admin"),
            )
        return redirect(4, "Administrator created. Password stored as a salted PBKDF2 hash.")

    @router.post("/onboarding/finish")
    async def finish_onboarding():
        profile = _primary_profile(db)
        warnings = schedule.validate(profile["id"])
        blocking = [warning for warning in warnings if warning.level.lower() == "error"]
        if blocking:
            raise HTTPException(400, "Resolve validation errors before finishing onboarding")
        db.update_settings({"onboarding_completed": True})
        schedule.rebuild_profile(profile["id"])
        return RedirectResponse(f"/profile/{profile['id']}?message=Setup+complete", 303)

    @router.post("/onboarding/reset")
    async def reset_onboarding():
        db.update_settings({"onboarding_completed": False})
        return RedirectResponse("/onboarding", 303)

    @router.get("/backup/database")
    async def backup_database():
        _, name = tempfile.mkstemp(prefix="school-day-grid-", suffix=".sqlite3")
        Path(name).unlink(missing_ok=True)
        with sqlite3.connect(db.path) as source, sqlite3.connect(name) as target:
            source.backup(target)
        Path(name).chmod(0o600)
        return FileResponse(
            name,
            media_type="application/vnd.sqlite3",
            filename=f"school-day-grid-backup-{date.today().isoformat()}.sqlite3",
            background=BackgroundTask(lambda: Path(name).unlink(missing_ok=True)),
        )

    @router.get("/manifest.webmanifest")
    async def manifest():
        return JSONResponse(
            {
                "name": "School Day Grid",
                "short_name": "Day Grid",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#f6f7fb",
                "theme_color": "#1675e5",
                "icons": [
                    {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
                ],
            },
            media_type="application/manifest+json",
        )

    @router.get("/service-worker.js")
    async def service_worker():
        script = """const CACHE='sdg-v2';const CORE=['/manifest.webmanifest','/static/images/school-day-grid-logo.png','/static/icons/icon-192.png','/static/icons/icon-512.png'];self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE))));self.addEventListener('fetch',e=>{if(e.request.method==='GET')e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r}).catch(()=>caches.match(e.request)))})"""
        return Response(script, media_type="application/javascript")

    return router
