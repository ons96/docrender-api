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
