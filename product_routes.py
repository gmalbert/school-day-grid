"""Product-facing routes implementing the distributable feature set."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import re
import secrets
from calendar import Calendar
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.templating import Jinja2Templates

from adapters import ICSUrlSource, NtfyPublisher, WebhookNotificationPublisher
from database import Database
from schedule import ScheduleService


WEEKDAY_NAMES = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")


def short_date(value: str) -> str:
    day = date.fromisoformat(value)
    return f"{day.month}/{day.day}"


def schedule_calendar_weeks(rows: list[dict]) -> list[list[dict | None]]:
    """Place chronological schedule rows into Sunday-first calendar weeks."""
    weeks: list[list[dict | None]] = []
    week: list[dict | None] = [None] * 7
    for row in rows:
        day = date.fromisoformat(row["day"])
        weekday = (day.weekday() + 1) % 7  # Python starts weeks on Monday.
        if weekday == 0 and any(week):
            weeks.append(week)
            week = [None] * 7
        cell = dict(row)
        cell["display_day"] = short_date(row["day"])
        week[weekday] = cell
        if weekday == 6:
            weeks.append(week)
            week = [None] * 7
    if any(week):
        weeks.append(week)
    return weeks


def schedule_view_data(rows: list[dict], view: str, focus: str = "") -> dict:
    """Build the all-weeks, month, week, and work-week calendar presentations."""
    selected_view = view if view in {"all", "month", "week", "weekdays"} else "all"
    try:
        focused_day = date.fromisoformat(focus) if focus else date.today()
    except ValueError:
        focused_day = date.today()
    if selected_view == "all":
        return {
            "selected_view": selected_view,
            "title": "",
            "weeks": schedule_calendar_weeks(rows),
            "headers": WEEKDAY_NAMES,
            "columns": 7,
            "previous_focus": "",
            "next_focus": "",
        }

    by_day = {row["day"]: row for row in rows}

    def cell(day: date) -> dict | None:
        row = by_day.get(day.isoformat())
        if not row:
            return None
        value = dict(row)
        value["display_day"] = short_date(row["day"])
        return value

    if selected_view == "month":
        month_start = focused_day.replace(day=1)
        weeks = [[cell(day) for day in week] for week in Calendar(firstweekday=6).monthdatescalendar(month_start.year, month_start.month)]
        previous_focus = (month_start - timedelta(days=1)).replace(day=1)
        next_focus = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return {
            "selected_view": selected_view,
            "title": month_start.strftime("%B %Y"),
            "weeks": weeks,
            "headers": WEEKDAY_NAMES,
            "columns": 7,
            "previous_focus": previous_focus.isoformat(),
            "next_focus": next_focus.isoformat(),
        }

    week_start = focused_day - timedelta(days=(focused_day.weekday() + 1) % 7)
    if selected_view == "weekdays":
        days = [week_start + timedelta(days=offset) for offset in range(1, 6)]
        return {
            "selected_view": selected_view,
            "title": f"Week of {short_date(week_start.isoformat())}",
            "weeks": [[cell(day) for day in days]],
            "headers": WEEKDAY_NAMES[1:6],
            "columns": 5,
            "previous_focus": (week_start - timedelta(days=7)).isoformat(),
            "next_focus": (week_start + timedelta(days=7)).isoformat(),
        }

    days = [week_start + timedelta(days=offset) for offset in range(7)]
    return {
        "selected_view": selected_view,
        "title": f"Week of {short_date(week_start.isoformat())}",
        "weeks": [[cell(day) for day in days]],
        "headers": WEEKDAY_NAMES,
        "columns": 7,
        "previous_focus": (week_start - timedelta(days=7)).isoformat(),
        "next_focus": (week_start + timedelta(days=7)).isoformat(),
    }


def slugify(value:str)->str:
    return re.sub(r"[^a-z0-9]+","-",value.lower()).strip("-") or "calendar"

def password_hash(password:str,salt:str|None=None)->str:
    salt=salt or secrets.token_hex(16); digest=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),240000); return f"pbkdf2_sha256${salt}${digest.hex()}"
def verify_password(password:str,stored:str)->bool:
    try: _,salt,digest=stored.split("$",2); return hmac.compare_digest(password_hash(password,salt).split("$")[-1],digest)
    except ValueError:return False

class Extras:
    def __init__(self,db:Database):self.db=db
    def add_rule(self,pid,name,weekday,start_date="",end_date="",nth=None,month=None):
        with self.db._connect() as c:c.execute("INSERT INTO closure_rules(profile_id,name,weekday,start_date,end_date,nth,month) VALUES(?,?,?,?,?,?,?)",(pid,name,weekday,start_date or None,end_date or None,nth,month))
        self.db.audit(pid,"closure_rule_added",{"name":name,"weekday":weekday})
    def add_source(self,pid,name,url,include,exclude):
        with self.db._connect() as c:c.execute("INSERT INTO external_sources(profile_id,source_type,name,url,include_terms,exclude_terms) VALUES(?,?,?,?,?,?)",(pid,"ics_url",name,url,json.dumps(include),json.dumps(exclude)))
        self.db.audit(pid,"source_added",{"name":name,"url":url})
    def sources(self,pid):
        with self.db._connect() as c:return [dict(r) for r in c.execute("SELECT * FROM external_sources WHERE profile_id=? ORDER BY id",(pid,))]
    def source(self,sid):
        with self.db._connect() as c:r=c.execute("SELECT * FROM external_sources WHERE id=?",(sid,)).fetchone(); return dict(r) if r else None
    def mark_source(self,sid,digest):
        with self.db._connect() as c:c.execute("UPDATE external_sources SET last_checked=?,last_hash=? WHERE id=?",(datetime.now(timezone.utc).isoformat(),digest,sid))
    def targets(self,pid):
        with self.db._connect() as c:return [dict(r) for r in c.execute("SELECT * FROM notification_targets WHERE profile_id=? AND enabled=1",(pid,))]
    def add_target(self,pid,kind,name,config):
        with self.db._connect() as c:c.execute("INSERT INTO notification_targets(profile_id,kind,name,config) VALUES(?,?,?,?)",(pid,kind,name,json.dumps(config)))
    def users(self):
        with self.db._connect() as c:return [dict(r) for r in c.execute("SELECT id,username,role,created_at FROM users")]
    def ensure_user(self,username,password):
        with self.db._connect() as c:
            if c.execute("SELECT 1 FROM users WHERE username=?",(username,)).fetchone(): return False
            c.execute("INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",(username,password_hash(password),"admin",datetime.now(timezone.utc).isoformat())); return True
    def authenticate(self,username,password):
        with self.db._connect() as c:r=c.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
        return dict(r) if r and verify_password(password,r["password_hash"]) else None


def build_product_router(db:Database,schedule:ScheduleService,templates:Jinja2Templates)->APIRouter:
    router=APIRouter(); extra=Extras(db)
    def go(path="/",message=""): return RedirectResponse(path+("?message="+quote(message) if message else ""),303)

    @router.get("/api/v1/profiles")
    async def profiles(): return db.profiles()
    @router.post("/profiles")
    async def create_profile(name:str=Form(...),slug:str=Form(""),school_year_start:str=Form(""),school_year_end:str=Form(""),cycle_labels:str=Form("Day 1\nDay 2\nDay 3\nDay 4\nDay 5")):
        labels=[x.strip() for x in cycle_labels.splitlines() if x.strip()]; pid=db.create_profile(name,slugify(slug or name),school_year_start,school_year_end,cycle_labels=labels); 
        if school_year_start and school_year_end:schedule.rebuild_profile(pid)
        return go(f"/profile/{pid}","Profile created.")

    @router.get("/profile/{profile}",response_class=HTMLResponse)
    async def profile_view(request:Request,profile:str,message:str="",view:str="all",focus:str=""):
        p=db.profile(profile)
        if not p: raise HTTPException(404,"Profile not found")
        today=schedule.today(profile=p["id"]); today_row=dict(today); today_row["display_day"]=short_date(today_row["day"])
        nxt=schedule.next_school_day(profile=p["id"]); next_school=dict(nxt) if nxt else None
        if next_school: next_school["display_day"]=short_date(next_school["day"])
        rows=schedule.rows(profile=p["id"]); calendar_view=schedule_view_data(rows,view,focus); warnings=schedule.validate(p["id"])
        return templates.TemplateResponse(request,"profile.html",{"profile":p,"cycles":db.cycles(p["id"]),"today_row":today_row,"next_school":next_school,"rows":rows,"calendar_weeks":calendar_view["weeks"],"weekday_names":calendar_view["headers"],"calendar_view":calendar_view,"warnings":warnings,"audit":db.audit_rows(p["id"],20),"sources":extra.sources(p["id"]),"message":message})

    @router.get("/help", response_class=HTMLResponse)
    async def help_page(request: Request):
        return templates.TemplateResponse(request, "help.html", {})

    @router.post("/profile/{profile}/cycles")
    async def cycles(profile:str,labels:list[str]=Form(...)):
        p=db.profile(profile); db.set_cycles(p["id"],[x.strip() for x in labels if x.strip()]); schedule.rebuild_profile(p["id"]); return go(f"/profile/{p['id']}","Cycle-day activities updated.")
    @router.post("/profile/{profile}/snow-day")
    async def snow_day(profile:str,day:str=Form(...),title:str=Form("Snow Day")):
        p=db.profile(profile); schedule.add_snow_day_and_shift(p["id"],date.fromisoformat(day),title); return go(f"/profile/{p['id']}",f"{day} added; remaining cycle shifted automatically.")
    @router.post("/profile/{profile}/override")
    async def override(profile:str,day:str=Form(...),override_type:str=Form(...),cycle_day:int|None=Form(None),title:str=Form(""),note:str=Form("")):
        p=db.profile(profile); db.set_override(p["id"],day,override_type,cycle_day,title,note); schedule.rebuild_profile(p["id"]); return go(f"/profile/{p['id']}","Date override applied.")
    @router.post("/profile/{profile}/closure-rule")
    async def closure_rule(profile:str,name:str=Form(...),weekday:int=Form(...),start_date:str=Form(""),end_date:str=Form(""),nth:int|None=Form(None),month:int|None=Form(None)):
        p=db.profile(profile); extra.add_rule(p["id"],name,weekday,start_date,end_date,nth,month); schedule.rebuild_profile(p["id"]); return go(f"/profile/{p['id']}","Recurring closure rule added.")

    @router.get("/api/v1/profiles/{profile}/preview")
    async def preview(profile:str):
        rows,summary=schedule.preview(profile); return {"summary":{"school_days":summary.school_days,"non_school_days":summary.non_school_days,"weekend_days":summary.weekend_days,"start":summary.start.isoformat(),"end":summary.end.isoformat()},"warnings":schedule.validate(profile),"schedule":rows}
    @router.get("/api/v1/profiles/{profile}/validation")
    async def validation(profile:str):return schedule.validate(profile)
    @router.post("/profile/{profile}/undo")
    async def undo(profile:str):
        p=db.profile(profile); ok=db.undo(p["id"]); 
        if ok:schedule.rebuild_profile(p["id"])
        return go(f"/profile/{p['id']}","Last change undone." if ok else "No snapshot available.")

    @router.get("/household",response_class=HTMLResponse)
    async def household(request:Request):
        cards=[]
        for p in db.profiles(): cards.append({"profile":p,"today":schedule.today(profile=p["id"]),"next":schedule.next_school_day(profile=p["id"])})
        return templates.TemplateResponse(request,"household.html",{"cards":cards})
    @router.get("/share/{token}",response_class=HTMLResponse)
    async def shared(request:Request,token:str):
        p=db.token_profile(token)
        if not p: raise HTTPException(404,"Share link not found")
        rows=schedule.rows(profile=p["id"])
        return templates.TemplateResponse(request,"shared.html",{"profile":p,"today":schedule.today(profile=p["id"]),"next":schedule.next_school_day(profile=p["id"]),"rows":rows,"calendar_weeks":schedule_calendar_weeks(rows),"weekday_names":WEEKDAY_NAMES})
    @router.get("/calendar/{slug}.ics")
    async def private_ics(slug:str,token:str=""):
        p=db.profile(slug)
        if not p or not token or not hmac.compare_digest(token,p["ics_token"]): raise HTTPException(403,"Invalid calendar token")
        return Response(schedule.to_ics(p["id"]),media_type="text/calendar",headers={"Content-Disposition":f'inline; filename="{p["slug"]}.ics"'})

    @router.post("/profile/{profile}/sources")
    async def add_source(profile:str,name:str=Form(...),url:str=Form(...),include_terms:str=Form("No School,School Closed,Vacation,Teacher Workday"),exclude_terms:str=Form("")):
        p=db.profile(profile); extra.add_source(p["id"],name,url,[x.strip() for x in include_terms.split(",") if x.strip()],[x.strip() for x in exclude_terms.split(",") if x.strip()]); return go(f"/profile/{p['id']}","Calendar URL source added.")
    @router.post("/sources/{source_id}/refresh")
    async def refresh_source(source_id:int):
        src=extra.source(source_id)
        if not src: raise HTTPException(404,"Source not found")
        source=ICSUrlSource(src["url"],json.loads(src["include_terms"]),json.loads(src["exclude_terms"])); events=await source.fetch_events(); digest=hashlib.sha256(json.dumps([(e.uid,e.summary,str(e.start),str(e.end)) for e in events]).encode()).hexdigest(); added=0
        for e in events:
            d=e.start
            while d < (e.end if e.end>e.start else date.fromordinal(e.start.toordinal()+1)):
                db.add_profile_non_school(src["profile_id"],d.isoformat(),"ics_url",e.summary,src["url"]); added+=1; d=date.fromordinal(d.toordinal()+1)
        extra.mark_source(source_id,digest); schedule.rebuild_profile(src["profile_id"]); return {"events":len(events),"dates_processed":added,"changed":digest!=src.get("last_hash")}

    @router.post("/profile/{profile}/notifications")
    async def add_notification(profile:str,kind:str=Form(...),name:str=Form(...),url:str=Form(...),topic:str=Form(""),token:str=Form("")):
        p=db.profile(profile); extra.add_target(p["id"],kind,name,{"url":url,"topic":topic,"token":token}); return go(f"/profile/{p['id']}","Notification target added.")
    @router.post("/profile/{profile}/notifications/test")
    async def test_notifications(profile:str):
        p=db.profile(profile); sent=0
        for target in extra.targets(p["id"]):
            cfg=json.loads(target["config"]); publisher=NtfyPublisher(cfg["url"],cfg.get("topic",p["slug"]),cfg.get("token","")) if target["kind"]=="ntfy" else WebhookNotificationPublisher(cfg["url"]); await publisher.send("School Day Grid",f"Notification test for {p['name']}",{"profile":p["slug"]}); sent+=1
        return {"sent":sent}

    @router.get("/login",response_class=HTMLResponse)
    async def login_page(request:Request):return templates.TemplateResponse(request,"login.html",{"has_users":bool(extra.users())})
    @router.post("/setup-admin")
    async def setup_admin(username:str=Form(...),password:str=Form(...)):
        if extra.users(): raise HTTPException(409,"Admin already exists")
        extra.ensure_user(username,password); return go("/login","Admin account created.")
    @router.post("/login")
    async def login(request:Request,username:str=Form(...),password:str=Form(...)):
        user=extra.authenticate(username,password)
        if not user:return go("/login","Invalid credentials.")
        request.session["user_id"]=user["id"];request.session["username"]=user["username"];return go("/","Signed in.")
    @router.post("/logout")
    async def logout(request:Request):request.session.clear();return go("/login","Signed out.")

    @router.get("/manifest.webmanifest")
    async def manifest():return JSONResponse({"name":"School Day Grid","short_name":"Day Grid","start_url":"/","display":"standalone","background_color":"#f6f7fb","theme_color":"#263a63","icons":[{"src":"/static/icons/icon-192.svg","sizes":"192x192","type":"image/svg+xml","purpose":"any maskable"},{"src":"/static/icons/icon-512.svg","sizes":"512x512","type":"image/svg+xml","purpose":"any maskable"}]},media_type="application/manifest+json")
    @router.get("/service-worker.js")
    async def service_worker():
        js="""const CACHE='sdg-v1'; self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/','/manifest.webmanifest'])))); self.addEventListener('fetch',e=>{if(e.request.method==='GET')e.respondWith(fetch(e.request).then(r=>{let x=r.clone();caches.open(CACHE).then(c=>c.put(e.request,x));return r}).catch(()=>caches.match(e.request)))})"""; return Response(js,media_type="application/javascript")

    return router

async def subscription_refresh_loop(db:Database,schedule:ScheduleService,interval_seconds:int=21600):
    """Best-effort background refresh of configured ICS URL sources."""
    extra=Extras(db)
    while True:
        try:
            for p in db.profiles():
                for src in extra.sources(p["id"]):
                    if not src.get("enabled") or src.get("source_type")!="ics_url":continue
                    try:
                        source=ICSUrlSource(src["url"],json.loads(src["include_terms"]),json.loads(src["exclude_terms"])); events=await source.fetch_events(); digest=hashlib.sha256(json.dumps([(e.uid,e.summary,str(e.start),str(e.end)) for e in events]).encode()).hexdigest()
                        if digest!=src.get("last_hash"):
                            for e in events:
                                d=e.start; terminal=e.end if e.end>e.start else date.fromordinal(e.start.toordinal()+1)
                                while d<terminal: db.add_profile_non_school(p["id"],d.isoformat(),"ics_url",e.summary,src["url"]); d=date.fromordinal(d.toordinal()+1)
                            schedule.rebuild_profile(p["id"])
                        extra.mark_source(src["id"],digest)
                    except Exception as exc: db.audit(p["id"],"source_refresh_failed",{"source":src["id"],"error":str(exc)})
        finally: await asyncio.sleep(interval_seconds)
