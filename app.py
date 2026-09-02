"""docrender-api: boring doc/image conversion API."""
# ponytail: single file until a 3rd endpoint forces a package.
import io
import os
import sqlite3
from datetime import date

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import Response

KEYS = {k.strip() for k in os.getenv("DOCRENDER_API_KEYS", "dev-key").split(",") if k.strip()}
CAP = int(os.getenv("DOCRENDER_DAILY_CAP", "100"))
DB = os.getenv("DOCRENDER_DB", "data/usage.db")

app = FastAPI(title="docrender-api")


def _db():
    d = os.path.dirname(DB)
    if d:
        os.makedirs(d, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS usage (k TEXT, d TEXT, n INT, PRIMARY KEY (k, d))")
    return c


def key_ok(x_api_key: str = Header(default="")) -> str:
    if x_api_key not in KEYS:
        raise HTTPException(401, "bad or missing X-API-Key")
    c = _db()
    today = date.today().isoformat()
    row = c.execute("SELECT n FROM usage WHERE k=? AND d=?", (x_api_key, today)).fetchone()
    n = row[0] if row else 0
    if n >= CAP:
        c.close()
        raise HTTPException(429, "daily cap reached")
    c.execute("INSERT OR REPLACE INTO usage VALUES (?,?,?)", (x_api_key, today, n + 1))
    c.commit()
    c.close()
    return x_api_key


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/v1/convert/image")
def convert_image(
    w: int = 0, h: int = 0, fmt: str = "PNG",
    f: UploadFile = File(...), _=Depends(key_ok),
):
    from PIL import Image
    fmt = fmt.upper()
    if fmt not in ("PNG", "JPEG", "JPG", "WEBP"):
        raise HTTPException(400, "fmt must be PNG/JPEG/WEBP")
    img = Image.open(f.file)
    if fmt in ("JPEG", "JPG"):
        img = img.convert("RGB")
    if w > 0 or h > 0:
        img.thumbnail((w or img.width, h or img.height))
    buf = io.BytesIO()
    img.save(buf, fmt)
    mt = "jpeg" if fmt == "JPG" else fmt.lower()
    return Response(buf.getvalue(), media_type=f"image/{mt}")


@app.post("/v1/render/pdf")
def render_pdf(payload: dict, _=Depends(key_ok)):
    from fpdf import FPDF
    text = payload.get("text", "")
    if not text or len(text) > 50000:
        raise HTTPException(400, "text required, max 50000 chars")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, text)
    return Response(bytes(pdf.output()), media_type="application/pdf")
