import io
import os

os.environ.setdefault("DOCRENDER_API_KEYS", "test-key")
os.environ["DOCRENDER_DB"] = "/tmp/opencode/docrender-test.db"
try:
    os.remove("/tmp/opencode/docrender-test.db")
except FileNotFoundError:
    pass

from fastapi.testclient import TestClient

from app import app

c = TestClient(app)
H = {"X-API-Key": "test-key"}


def test_health():
    assert c.get("/health").json() == {"ok": True}


def test_unauth():
    assert c.post("/v1/render/pdf", json={"text": "hi"}).status_code == 401


def test_pdf():
    r = c.post("/v1/render/pdf", json={"text": "hello"}, headers=H)
    assert r.status_code == 200 and r.content[:4] == b"%PDF"


def test_image():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "PNG")
    buf.seek(0)
    r = c.post("/v1/convert/image", files={"f": ("a.png", buf, "image/png")}, headers=H)
    assert r.status_code == 200
