from tests.conftest import REGISTER

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 2000


def test_site_and_health(client):
    assert client.get("/healthz").text == "ok"
    home = client.get("/")
    assert home.status_code == 200 and "Dog Everlasting" in home.text
    assert home.headers["cache-control"] == "no-cache"


def test_register_gets_private_likeness_link(client):
    res = client.post("/api/commissions", json=REGISTER)
    url = res.json()["likeness_url"]
    assert url.startswith("/likeness/") and len(url) > 30
    page = client.get(url)
    assert page.status_code == 200 and "likeness" in page.text
    assert "noindex" in page.headers["x-robots-tag"]


def test_other_plans_have_no_likeness_link(client):
    body = {**REGISTER, "circumstance": "recent", "vet": "Park Animal Hospital, Rye"}
    assert client.post("/api/commissions", json=body).json()["likeness_url"] is None


def test_time_of_need_requires_vet(client):
    assert client.post("/api/commissions", json={**REGISTER, "circumstance": "recent"}).status_code == 422


def test_bad_email_rejected(client):
    assert client.post("/api/commissions", json={**REGISTER, "email": "nope"}).status_code == 422


def test_unknown_token_is_404(client):
    assert client.get("/likeness/not-a-real-token").status_code == 404
    assert client.get("/api/likeness/not-a-real-token").status_code == 404


def test_likeness_state_lists_every_slot_and_measurement(client, token):
    data = client.get(f"/api/likeness/{token}").json()
    assert data["dog"] == "Biscuit"
    keys = [s["key"] for g in data["groups"] for s in g["slots"]]
    assert {"front", "side_left", "eyes", "whiskers", "markings", "sitting", "walking"} <= set(keys)
    assert len(data["measurements"]["fields"]) == 10


def test_photo_upload_view_and_delete(client, token):
    res = client.post(f"/api/likeness/{token}/media", data={"slot": "front"}, files={"file": ("a.jpg", JPEG, "image/jpeg")})
    assert res.status_code == 201
    m = res.json()
    got = client.get(m["url"])
    assert got.status_code == 200 and got.content == JPEG
    slot = next(s for g in client.get(f"/api/likeness/{token}").json()["groups"] for s in g["slots"] if s["key"] == "front")
    assert len(slot["media"]) == 1
    assert client.delete(f"/api/likeness/{token}/media/{m['id']}").status_code == 204
    assert client.get(m["url"]).status_code == 404


def test_heic_sent_as_octet_stream_is_accepted(client, token):
    res = client.post(f"/api/likeness/{token}/media", data={"slot": "eyes"},
                      files={"file": ("IMG_0001.HEIC", b"heic-bytes", "application/octet-stream")})
    assert res.status_code == 201 and res.json()["content_type"] == "image/heic"


def test_wrong_type_for_slot_rejected(client, token):
    res = client.post(f"/api/likeness/{token}/media", data={"slot": "walking"}, files={"file": ("a.jpg", JPEG, "image/jpeg")})
    assert res.status_code == 415
    res = client.post(f"/api/likeness/{token}/media", data={"slot": "front"}, files={"file": ("x.exe", b"MZ", "application/x-msdownload")})
    assert res.status_code == 415


def test_unknown_slot_rejected(client, token):
    res = client.post(f"/api/likeness/{token}/media", data={"slot": "nope"}, files={"file": ("a.jpg", JPEG, "image/jpeg")})
    assert res.status_code == 400


def test_media_not_visible_through_another_token(client, token):
    m = client.post(f"/api/likeness/{token}/media", data={"slot": "front"}, files={"file": ("a.jpg", JPEG, "image/jpeg")}).json()
    other = client.post("/api/commissions", json=REGISTER).json()["likeness_url"].rsplit("/", 1)[1]
    assert client.get(f"/api/likeness/{other}/media/{m['id']}").status_code == 404
    assert client.delete(f"/api/likeness/{other}/media/{m['id']}").status_code == 404


def test_measurements_average_across_units(client, token):
    client.post(f"/api/likeness/{token}/measurements", json={"unit": "in", "taken_on": "2026-09-01", "values": {"neck": 10, "chest_girth": 20}})
    client.post(f"/api/likeness/{token}/measurements", json={"unit": "cm", "taken_on": "2026-09-05", "values": {"neck": 25.4}})
    m = client.get(f"/api/likeness/{token}").json()["measurements"]
    assert len(m["rounds"]) == 2
    assert m["average_cm"]["neck"] == 25.4
    assert m["average_cm"]["chest_girth"] == 50.8
    assert m["average_cm"]["head_width"] is None


def test_measurement_validation(client, token):
    url = f"/api/likeness/{token}/measurements"
    assert client.post(url, json={"unit": "cm", "values": {}}).status_code == 422
    assert client.post(url, json={"unit": "cm", "values": {"neck": -3}}).status_code == 422
    assert client.post(url, json={"unit": "cm", "values": {"tail_wag": 3}}).status_code == 422
    assert client.post(url, json={"unit": "furlong", "values": {"neck": 3}}).status_code == 422


def test_admin_requires_password(client, token):
    assert client.get("/admin").status_code == 401
    assert client.get("/admin", auth=("team", "wrong")).status_code == 401
    page = client.get("/admin", auth=("team", "test-admin"))
    assert page.status_code == 200 and "Biscuit" in page.text


def test_admin_escapes_user_input(client):
    evil = {**REGISTER, "dogName": "<script>alert(1)</script>"}
    cid = client.post("/api/commissions", json=evil).json()["id"]
    page = client.get(f"/admin/commissions/{cid}", auth=("team", "test-admin")).text
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;" in page
