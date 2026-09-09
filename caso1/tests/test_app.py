import app as application


def client(tmp_path, monkeypatch):
    monkeypatch.setattr(application, "DOWNLOAD_ROOT", tmp_path)
    application.app.config.update(TESTING=True)
    return application.app.test_client()


def test_home_renders(tmp_path, monkeypatch):
    response = client(tmp_path, monkeypatch).get("/")
    assert response.status_code == 200
    assert b"Droply" in response.data


def test_health(tmp_path, monkeypatch):
    response = client(tmp_path, monkeypatch).get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_rejects_unknown_domain(tmp_path, monkeypatch):
    response = client(tmp_path, monkeypatch).post(
        "/api/downloads", json={"url": "https://example.com/video", "quality": "720"}
    )
    assert response.status_code == 400


def test_accepts_supported_domain(tmp_path, monkeypatch):
    submitted = []
    monkeypatch.setattr(application.executor, "submit", lambda *args: submitted.append(args))
    response = client(tmp_path, monkeypatch).post(
        "/api/downloads", json={"url": "https://www.youtube.com/watch?v=test", "quality": "720"}
    )
    assert response.status_code == 202
    assert response.get_json()["status"] == "queued"
    assert len(submitted) == 1


def test_tiktok_uses_combined_format_with_fallback():
    url = "https://www.tiktok.com/@usuario/video/7673588558371835143"
    assert application.download_format(url, "720") == "best[height<=720]/best"
    assert application.download_format(url, "best") == "best"
    assert application.download_format(url, "audio") == "bestaudio/best"


def test_other_platforms_keep_split_audio_video_format():
    url = "https://www.youtube.com/watch?v=test"
    assert application.download_format(url, "720") == application.QUALITY_OPTIONS["720"]
