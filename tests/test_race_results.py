def test_race_win(client):
    r = client.post("/race", json={"problem_id": "two-sum", "user_time_ms": 1000})
    assert r.status_code == 200
    data = r.json()
    assert data["result"] == "win"
    assert data["problem_id"] == "two-sum"
    assert data["baseline_ms"] == 1200