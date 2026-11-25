def test_first_run_seeds_goals_and_starter_topics(client) -> None:
    assert "HIV" in client.get("/api/v1/profile").json()["goals"]
    names = [t["name"] for t in client.get("/api/v1/topics").json()]
    assert "AI for HIV & sexual health" in names


def test_topic_with_unknown_source_is_rejected(client) -> None:
    resp = client.post(
        "/api/v1/topics", json={"name": "X", "queries": ["x"], "sources": ["twitter"]}
    )
    assert resp.status_code == 422


def test_topic_can_be_created_and_deleted(client) -> None:
    created = client.post(
        "/api/v1/topics", json={"name": "Mpox", "queries": ["mpox vaccine"], "sources": ["news"]}
    ).json()
    assert created["queries"] == ["mpox vaccine"]
    assert client.delete(f"/api/v1/topics/{created['id']}").status_code == 204


def test_goals_can_be_updated(client) -> None:
    client.put("/api/v1/profile", json={"goals": "Build CV models for STI screening"})
    assert client.get("/api/v1/profile").json()["goals"] == "Build CV models for STI screening"
