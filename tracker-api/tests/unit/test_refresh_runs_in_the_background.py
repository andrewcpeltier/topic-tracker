import time

from app.pipeline import job


def test_refresh_starts_a_background_job_that_finishes(client) -> None:
    started = client.post("/api/v1/refresh?fetch=false")
    assert started.status_code == 202

    for _ in range(50):
        status = client.get("/api/v1/status").json()
        if not status["running"]:
            break
        time.sleep(0.05)

    assert status["running"] is False
    assert status["last_result"] is not None
    assert job.phase == "idle"
