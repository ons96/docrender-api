"""docrender-api: boring doc/image conversion API. One file. See docs/specs/docrender-api.md."""
import io
import os
import secrets
import sqlite3
from datetime import date

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

DB = os.environ.get("DOCRENDER_DB", os.path.join(os.path.dirname(__file__), "usage.db"))


def _cap() -> int:
    return int(os.environ.get("DOCRENDER_DAILY_CAP", "100"))


def _db() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS usage (key TEXT, day TEXT, n INT, PRIMARY KEY (key, day))")
    con.execute("CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, label TEXT)")
    return con


def _valid(user_key: str) -> bool:
    if user_key in os.environ.get("DOCRENDER_API_KEYS", "").split(","):
        return True
    con = _db()
    try:
        return con.execute("SELECT 1 FROM keys WHERE key=?", (user_key,)).fetchone() is not None
    finally:
        con.close()


def _check(user_key: str) -> None:
    if not user_key or not _valid(user_key):
        raise HTTPException(401, "bad key")
    con = _db()
    try:
        row = con.execute("SELECT n FROM usage WHERE key=? AND day=?", (user_key, str(date.today()))).fetchone()
        if row and row[0] >= _cap():
            raise HTTPException(429, "daily cap reached")
        con.execute("INSERT OR IGNORE INTO usage VALUES (?,?,0)", (user_key, str(date.today())))
        con.execute("UPDATE usage SET n=n+1 WHERE key=? AND day=?", (user_key, str(date.today())))
        con.commit()
    finally:
        con.close()


app = FastAPI(title="docrender-api")


class PDFIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class ImgIn(BaseModel):
    url: str = Field(min_length=8, max_length=2000)
    width: int = Field(default=800, ge=16, le=4000)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/v1/usage")
def usage(x_api_key: str = Header(default="")):
    if not _valid(x_api_key):
        raise HTTPException(401, "bad key")
    con = _db()
    try:
        row = con.execute("SELECT n FROM usage WHERE key=? AND day=?", (x_api_key, str(date.today()))).fetchone()
        return {"used": (row or [0])[0], "cap": _cap(), "day": str(date.today())}
    finally:
        con.close()


@app.get("/", response_class=HTMLResponse)
def landing():
    return """<h1>docrender-api</h1><p>Boring doc/image conversion over HTTPS. No SDK, no dashboard, just curl.</p>
<pre>curl -X POST $HOST/v1/render/pdf -H "X-API-Key: KEY" -d '{"text":"hi"}'</pre>
<p>Endpoints: POST /v1/render/pdf, POST /v1/convert/image, GET /v1/usage. Free tier 100/day.</p>"""


@app.post("/v1/render/pdf")
def render_pdf(body: PDFIn, x_api_key: str = Header(default="")):
    _check(x_api_key)
    from fpdf import FPDF  # ponytail: lazy import, keeps /health light

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, body.text)
    return Response(bytes(pdf.output()), media_type="application/pdf")


@app.post("/v1/convert/image")
def convert_image(body: ImgIn, x_api_key: str = Header(default="")):
    _check(x_api_key)
    import urllib.request  # ponytail: stdlib fetch, no new dep

    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(400, "http(s) only")
    try:
        with urllib.request.urlopen(body.url, timeout=15) as r:
            raw = r.read(8_000_000)
    except Exception:
        raise HTTPException(400, "fetch failed")
    from PIL import Image  # ponytail: lazy import, keeps /health light

    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        raise HTTPException(400, "not an image")
    img.thumbnail((body.width, body.width * 4))
    out = io.BytesIO()
    img.save(out, "PNG")
    return Response(out.getvalue(), media_type="image/png")


class ProvIn(BaseModel):
    label: str = Field(default="", max_length=80)


@app.post("/v1/admin/provision")
def provision(body: ProvIn, x_admin_key: str = Header(default="")):
    if not x_admin_key or x_admin_key != os.environ.get("DOCRENDER_ADMIN_KEY", ""):
        raise HTTPException(401, "bad admin key")
    key = "dr_" + secrets.token_hex(12)
    con = _db()
    try:
        con.execute("INSERT INTO keys VALUES (?,?)", (key, body.label))
        con.commit()
    finally:
        con.close()
    return {"key": key}


@app.post("/v1/admin/revoke")
def revoke(body: dict, x_admin_key: str = Header(default="")):
    if not x_admin_key or x_admin_key != os.environ.get("DOCRENDER_ADMIN_KEY", ""):
        raise HTTPException(401, "bad admin key")
    con = _db()
    try:
        con.execute("DELETE FROM keys WHERE key=?", (body.get("key", ""),))
        con.commit()
    finally:
        con.close()
    return {"ok": True}
