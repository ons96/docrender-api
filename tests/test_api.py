import os
import sqlite3

os.environ["DOCRENDER_API_KEYS"] = "t1"
os.environ["DOCRENDER_ADMIN_KEY"] = "adm"
os.environ["DOCRENDER_DB"] = "/tmp/docrender-test.db"
if os.path.exists("/tmp/docrender-test.db"):
    os.unlink("/tmp/docrender-test.db")

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402

c = TestClient(app.app)
H = {"X-API-Key": "t1"}


def test_health():
    assert c.get("/health").json() == {"ok": True}


def test_pdf_ok_and_auth():
    r = c.post("/v1/render/pdf", json={"text": "hi"}, headers=H)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert c.post("/v1/render/pdf", json={"text": "hi"}).status_code == 401


def test_usage_counts():
    r = c.get("/v1/usage", headers=H).json()
    assert r["used"] >= 1 and r["cap"] == 100


def test_admin_provision_revoke_cycle():
    AH = {"X-Admin-Key": "adm"}
    key = c.post("/v1/admin/provision", json={"label": "shop"}, headers=AH).json()["key"]
    assert c.post("/v1/render/pdf", json={"text": "x"}, headers={"X-API-Key": key}).status_code == 200
    assert c.post("/v1/admin/revoke", json={"key": key}, headers=AH).json() == {"ok": True}
    assert c.post("/v1/render/pdf", json={"text": "x"}, headers={"X-API-Key": key}).status_code == 401
    assert c.post("/v1/admin/provision", json={}, headers={"X-Admin-Key": "no"}).status_code == 401


def test_cap_429():
    os.environ["DOCRENDER_DAILY_CAP"] = "1"
    con = sqlite3.connect("/tmp/docrender-test.db")
    con.execute("DELETE FROM usage WHERE key='t1'")
    con.commit()
    con.close()
    assert c.post("/v1/render/pdf", json={"text": "a"}, headers=H).status_code == 200
    assert c.post("/v1/render/pdf", json={"text": "b"}, headers=H).status_code == 429
    del os.environ["DOCRENDER_DAILY_CAP"]


def test_rapidapi_key_requires_proxy_secret():
    os.environ["DOCRENDER_RAPIDAPI_SECRET"] = "rs"
    RH = {"X-RapidAPI-Key": "r1", "X-RapidAPI-Proxy-Secret": "rs"}
    assert c.post("/v1/render/pdf", json={"text": "hi"}, headers=RH).status_code == 200
    assert c.get("/v1/usage", headers=RH).status_code == 200
    assert c.post("/v1/render/pdf", json={"text": "hi"}, headers={"X-RapidAPI-Key": "r1"}).status_code == 401
    assert (
        c.post(
            "/v1/render/pdf",
            json={"text": "hi"},
            headers={"X-RapidAPI-Key": "r1", "X-RapidAPI-Proxy-Secret": "wrong"},
        ).status_code
        == 401
    )
    assert c.post("/v1/render/pdf", json={"text": "hi"}, headers=H).status_code == 200
    del os.environ["DOCRENDER_RAPIDAPI_SECRET"]


def test_convert_image_resizes_and_rejects_non_http():
    import http.server
    import io as _io
    import threading

    from PIL import Image as _Image

    buf = _io.BytesIO()
    _Image.new("RGB", (1200, 900), (200, 30, 30)).save(buf, "JPEG")
    payload = buf.getvalue()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        url = "http://127.0.0.1:%d/a.jpg" % srv.server_address[1]
        r = c.post("/v1/convert/image", json={"url": url, "width": 100}, headers=H)
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "image/png"
        out = _Image.open(_io.BytesIO(r.content))
        assert out.width <= 100 and out.height <= 400
    finally:
        srv.shutdown()
    assert c.post("/v1/convert/image", json={"url": "file:///etc/passwd"}, headers=H).status_code == 400


def test_openapi_declares_rapidapi_scheme():
    spec = c.get("/openapi.json").json()
    assert spec["components"]["securitySchemes"]["RapidApiKey"]["name"] == "X-RapidAPI-Key"
    assert spec["paths"]["/v1/render/pdf"]["post"]["security"][0] == {"RapidApiKey": []}
