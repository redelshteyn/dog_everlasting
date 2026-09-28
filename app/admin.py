"""Plain, password-protected pages for the team to see requests, uploads and measurements."""

from html import escape as e

from app.catalog import MEASUREMENTS, SLOTS
from app.models import Commission

PLANS = {"recent": "At Time of Need", "register": "The Register", "ahead": "Consultation"}

STYLE = """<style>
body{font:14px/1.5 -apple-system,Helvetica,Arial,sans-serif;margin:40px;color:#000}
h1{font-weight:400;letter-spacing:.2em;font-size:16px;text-transform:uppercase}
h2{font-weight:400;font-size:20px;margin:40px 0 12px}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:8px 12px 8px 0;border-bottom:1px solid #e3e3e3;vertical-align:top}
th{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#6f6f6f;font-weight:400}
a{color:#000}.muted{color:#6f6f6f}.grid{display:flex;flex-wrap:wrap;gap:12px}
figure{margin:0;width:180px}figure img,figure video{width:180px;height:180px;object-fit:cover;background:#eee;display:block}
figcaption{font-size:12px;color:#6f6f6f;margin-top:4px}
</style>"""


def page(title: str, body: str) -> str:
    return f"<!doctype html><meta charset=utf-8><meta name=robots content=noindex><title>{e(title)}</title>{STYLE}<h1>Dog Everlasting</h1>{body}"


def list_page(rows: list[Commission]) -> str:
    trs = "".join(
        f"<tr><td>{c.created_at:%Y-%m-%d %H:%M}</td><td>{e(PLANS.get(c.plan, c.plan))}</td>"
        f"<td><a href='/admin/commissions/{c.id}'>{e(c.dog_name)}</a></td><td>{e(c.tier)}</td>"
        f"<td>{e(c.name)}<br><span class=muted>{e(c.email)} · {e(c.phone)}</span></td><td>{e(c.vet)}</td>"
        f"<td>{len(c.media)}</td><td>{len(c.measurements)}</td></tr>"
        for c in rows)
    return page("Requests", "<h2>Requests</h2><table><tr><th>Received</th><th>Plan</th><th>Dog</th><th>Commission</th>"
                f"<th>Owner</th><th>Veterinarian</th><th>Files</th><th>Rounds</th></tr>{trs}</table>"
                + ("" if rows else "<p class=muted>Nothing yet.</p>"))


def detail_page(c: Commission, avg_cm: dict) -> str:
    facts = [("Plan", PLANS.get(c.plan, c.plan)), ("Received", f"{c.created_at:%Y-%m-%d %H:%M}"), ("Dog", c.dog_name),
             ("Breed", c.breed), ("Commission", c.tier), ("Pose", c.pose), ("Owner", c.name), ("Email", c.email),
             ("Telephone", c.phone), ("City", c.city), ("Preferred contact", c.contact), ("Veterinarian", c.vet),
             ("In their words", c.story)]
    body = f"<p><a href='/admin'>← All requests</a></p><h2>{e(c.dog_name)}</h2><table>"
    body += "".join(f"<tr><th>{e(k)}</th><td>{e(v or '—')}</td></tr>" for k, v in facts)
    if c.token:
        body += f"<tr><th>Likeness page</th><td><a href='/likeness/{e(c.token)}'>/likeness/{e(c.token)}</a></td></tr>"
    body += "</table>"

    body += f"<h2>Photographs and film ({len(c.media)})</h2><div class=grid>"
    for m in c.media:
        src = f"/admin/media/{m.id}"
        if m.kind == "video":
            thumb = f"<video src='{src}' controls preload=metadata></video>"
        elif m.content_type in ("image/heic", "image/heif"):
            thumb = f"<a href='{src}'>Download HEIC</a>"
        else:
            thumb = f"<a href='{src}'><img src='{src}' alt=''></a>"
        label = SLOTS.get(m.slot, {}).get("label", m.slot)
        body += f"<figure>{thumb}<figcaption>{e(label)}<br>{m.created_at:%Y-%m-%d}</figcaption></figure>"
    body += "</div>" + ("" if c.media else "<p class=muted>None yet.</p>")

    body += f"<h2>Measurements ({len(c.measurements)} rounds)</h2>"
    if c.measurements:
        head = "".join(f"<th>{e(label)}</th>" for _, label, _ in MEASUREMENTS)
        body += f"<table><tr><th>Date</th>{head}<th>Notes</th></tr>"
        for r in c.measurements:
            cells = "".join(f"<td>{'' if v is None else f'{v:g} {r.unit}'}</td>" for v in r.values().values())
            body += f"<tr><td>{r.taken_on}</td>{cells}<td>{e(r.notes)}</td></tr>"
        avg = "".join(f"<td><b>{'' if v is None else f'{v:g} cm'}</b></td>" for v in avg_cm.values())
        body += f"<tr><td><b>Average</b></td>{avg}<td></td></tr></table>"
    else:
        body += "<p class=muted>None yet.</p>"
    return page(c.dog_name, body)
