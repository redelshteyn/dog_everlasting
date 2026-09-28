import re
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app import admin, config
from app.catalog import IMAGE_TYPES, MEASUREMENTS, MEASUREMENT_KEYS, SLOT_GROUPS, SLOTS, UNITS, VIDEO_TYPES
from app.db import DATABASE_URL, get_db
from app.models import Commission, MeasurementSet, Media


def run_migrations() -> None:
    cfg = Config(str(config.ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(config.ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.check_production_config()
    config.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    run_migrations()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    # Browsers re-check on every visit, so deploys show up immediately.
    response.headers.setdefault("Cache-Control", "no-cache")
    if request.url.path.startswith(("/likeness", "/api/likeness", "/admin")):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


# ---------------------------------------------------------------- pages

@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/")
def home():
    return FileResponse(config.SITE_DIR / "index.html")


@app.get("/likeness/{token}")
def likeness_page(token: str, db: Session = Depends(get_db)):
    if not _commission_by_token(db, token):
        return HTMLResponse("<h1>This link is not valid.</h1><p>Please contact Dog Everlasting.</p>", status_code=404)
    return FileResponse(config.SITE_DIR / "likeness.html")


# ---------------------------------------------------------------- commissions

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class CommissionIn(BaseModel):
    circumstance: Literal["recent", "register", "ahead"]
    dogName: str = Field(min_length=1, max_length=120)
    breed: str = Field("", max_length=120)
    tier: Literal["petite", "signature", "grand", "unsure"]
    pose: str = Field("", max_length=60)
    story: str = Field("", max_length=5000)
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(max_length=254)
    phone: str = Field(min_length=7, max_length=40)
    city: str = Field("", max_length=120)
    contact: str = Field("", max_length=40)
    vet: str = Field("", max_length=240)

    @model_validator(mode="after")
    def check(self):
        for f in ("dogName", "name", "phone", "email", "vet", "breed", "city", "story"):
            setattr(self, f, getattr(self, f).strip())
        if not self.dogName or not self.name:
            raise ValueError("Name and dog's name are required.")
        if not EMAIL_RE.match(self.email):
            raise ValueError("Please enter a valid email.")
        if self.circumstance == "recent" and not self.vet:
            raise ValueError("Please tell us your veterinarian.")
        return self


@app.post("/api/commissions", status_code=201)
def create_commission(body: CommissionIn, db: Session = Depends(get_db)):
    c = Commission(
        plan=body.circumstance, dog_name=body.dogName, breed=body.breed, tier=body.tier, pose=body.pose,
        story=body.story, name=body.name, email=body.email, phone=body.phone, city=body.city,
        contact=body.contact, vet=body.vet,
        token=secrets.token_urlsafe(24) if body.circumstance == "register" else None,
    )
    db.add(c)
    db.commit()
    return {"id": c.id, "likeness_url": f"/likeness/{c.token}" if c.token else None}


# ---------------------------------------------------------------- likeness

def _commission_by_token(db: Session, token: str) -> Commission | None:
    if not token or len(token) > 64:
        return None
    return db.query(Commission).filter(Commission.token == token).one_or_none()


def commission_for(token: str, db: Session = Depends(get_db)) -> Commission:
    c = _commission_by_token(db, token)
    if not c:
        raise HTTPException(404, "Not found")
    return c


def media_json(token: str, m: Media) -> dict:
    return {"id": m.id, "kind": m.kind, "content_type": m.content_type, "name": m.original_name,
            "created_at": m.created_at.isoformat(), "url": f"/api/likeness/{token}/media/{m.id}"}


def averages_cm(rounds: list[MeasurementSet]) -> dict[str, float | None]:
    out = {}
    for key in MEASUREMENT_KEYS:
        vals = [getattr(r, key) * UNITS[r.unit] for r in rounds if getattr(r, key) is not None]
        out[key] = round(sum(vals) / len(vals), 1) if vals else None
    return out


def round_json(r: MeasurementSet) -> dict:
    return {"id": r.id, "taken_on": r.taken_on.isoformat(), "unit": r.unit, "notes": r.notes, "values": r.values()}


@app.get("/api/likeness/{token}")
def get_likeness(token: str, c: Commission = Depends(commission_for)):
    by_slot: dict[str, list] = {}
    for m in c.media:
        by_slot.setdefault(m.slot, []).append(media_json(token, m))
    return {
        "dog": c.dog_name,
        "owner_first": c.name.split()[0] if c.name else "",
        "groups": [
            {"name": group, "kind": kind,
             "slots": [{"key": k, "label": label, "hint": hint, "media": by_slot.get(k, [])} for k, label, hint in items]}
            for group, kind, items in SLOT_GROUPS
        ],
        "measurements": {
            "fields": [{"key": k, "label": label, "hint": hint} for k, label, hint in MEASUREMENTS],
            "rounds": [round_json(r) for r in c.measurements],
            "average_cm": averages_cm(c.measurements),
        },
    }


def _content_type(slot_kind: str, upload: UploadFile) -> tuple[str, str]:
    """Return (content_type, extension). Phones sometimes send HEIC/MOV as octet-stream, so fall back to the extension."""
    allowed = IMAGE_TYPES if slot_kind == "photo" else VIDEO_TYPES
    ctype = (upload.content_type or "").lower()
    if ctype in allowed:
        return ctype, allowed[ctype]
    ext = "." + (upload.filename or "").rsplit(".", 1)[-1].lower() if "." in (upload.filename or "") else ""
    ext = {".jpeg": ".jpg"}.get(ext, ext)
    for t, e in allowed.items():
        if e == ext:
            return t, e
    if slot_kind == "photo":
        raise HTTPException(415, "Please add a photograph here (JPEG, PNG or HEIC).")
    raise HTTPException(415, "Please add a video here (MP4 or MOV).")


@app.post("/api/likeness/{token}/media", status_code=201)
async def upload_media(token: str, request: Request, slot: str = Form(...), file: UploadFile = File(...),
                       c: Commission = Depends(commission_for), db: Session = Depends(get_db)):
    if slot not in SLOTS:
        raise HTTPException(400, "Unknown view.")
    kind = SLOTS[slot]["kind"]
    limit = config.MAX_PHOTO_BYTES if kind == "photo" else config.MAX_VIDEO_BYTES
    if int(request.headers.get("content-length") or 0) > limit + 1024 * 1024:
        raise HTTPException(413, "That file is too large.")
    ctype, ext = _content_type(kind, file)

    stored = f"{uuid.uuid4().hex}{ext}"
    path = config.MEDIA_DIR / stored
    size = 0
    try:
        with path.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, "That file is too large.")
                out.write(chunk)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    if size == 0:
        path.unlink(missing_ok=True)
        raise HTTPException(400, "That file is empty.")

    m = Media(commission_id=c.id, slot=slot, kind=kind, original_name=(file.filename or "")[:255],
              stored_name=stored, content_type=ctype, size_bytes=size)
    db.add(m)
    db.commit()
    return media_json(token, m)


def _media(c: Commission, media_id: int) -> Media:
    m = next((m for m in c.media if m.id == media_id), None)
    if not m:
        raise HTTPException(404, "Not found")
    return m


@app.get("/api/likeness/{token}/media/{media_id}")
def get_media(media_id: int, c: Commission = Depends(commission_for)):
    m = _media(c, media_id)
    return FileResponse(config.MEDIA_DIR / m.stored_name, media_type=m.content_type,
                        headers={"Cache-Control": "private, max-age=86400"})


@app.delete("/api/likeness/{token}/media/{media_id}", status_code=204)
def delete_media(media_id: int, c: Commission = Depends(commission_for), db: Session = Depends(get_db)):
    m = _media(c, media_id)
    (config.MEDIA_DIR / m.stored_name).unlink(missing_ok=True)
    db.delete(m)
    db.commit()
    return Response(status_code=204)


class RoundIn(BaseModel):
    unit: Literal["in", "cm"]
    taken_on: date = Field(default_factory=date.today)
    notes: str = Field("", max_length=2000)
    values: dict[str, float | None]

    @model_validator(mode="after")
    def check(self):
        unknown = set(self.values) - set(MEASUREMENT_KEYS)
        if unknown:
            raise ValueError(f"Unknown measurement: {', '.join(sorted(unknown))}")
        present = {k: v for k, v in self.values.items() if v is not None}
        if not present:
            raise ValueError("Please enter at least one measurement.")
        for k, v in present.items():
            if not 0 < v * UNITS[self.unit] < 400:
                raise ValueError("One of those measurements looks out of range. Please check it.")
        return self


@app.post("/api/likeness/{token}/measurements", status_code=201)
def add_round(body: RoundIn, c: Commission = Depends(commission_for), db: Session = Depends(get_db)):
    r = MeasurementSet(commission_id=c.id, unit=body.unit, taken_on=body.taken_on, notes=body.notes.strip(),
                       **{k: body.values.get(k) for k in MEASUREMENT_KEYS})
    db.add(r)
    db.commit()
    return round_json(r)


@app.delete("/api/likeness/{token}/measurements/{round_id}", status_code=204)
def delete_round(round_id: int, c: Commission = Depends(commission_for), db: Session = Depends(get_db)):
    r = next((r for r in c.measurements if r.id == round_id), None)
    if not r:
        raise HTTPException(404, "Not found")
    db.delete(r)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------- admin

basic = HTTPBasic(realm="Dog Everlasting")


def require_admin(creds: HTTPBasicCredentials = Depends(basic)) -> None:
    if not secrets.compare_digest(creds.password.encode(), config.ADMIN_PASSWORD.encode()):
        raise HTTPException(401, "Unauthorized", headers={"WWW-Authenticate": 'Basic realm="Dog Everlasting"'})


@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_list(db: Session = Depends(get_db)):
    return admin.list_page(db.query(Commission).order_by(Commission.id.desc()).all())


@app.get("/admin/commissions/{commission_id}", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_detail(commission_id: int, db: Session = Depends(get_db)):
    c = db.get(Commission, commission_id)
    if not c:
        raise HTTPException(404, "Not found")
    return admin.detail_page(c, averages_cm(c.measurements))


@app.get("/admin/media/{media_id}", dependencies=[Depends(require_admin)])
def admin_media(media_id: int, db: Session = Depends(get_db)):
    m = db.get(Media, media_id)
    if not m:
        raise HTTPException(404, "Not found")
    return FileResponse(config.MEDIA_DIR / m.stored_name, media_type=m.content_type)
