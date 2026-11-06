def test_invalid_bet(client,auth_headers,session_id):
    r=client.get("/game",params={"session_id":session_id,"bet":100,"lines":1},headers=auth_headers)
    assert r.status_code==400
    assert r.json()["detail"]=="Bet must be between 500 and 10000"


def test_invalid_lines(client,auth_headers,session_id):
    r=client.get("/game",params={"session_id":session_id,"bet":500,"lines":6},headers=auth_headers)
    assert r.status_code==400
    assert r.json()["detail"]=="Lines must be between 1 and 5"


def test_invalid_session(client,auth_headers):
    r=client.get("/game",params={"session_id":"999999","bet":500,"lines":1},headers=auth_headers)
    assert r.status_code==404
    assert r.json()["detail"]=="Invalid session"


def test_insufficient_balance(client,auth_headers,session_id):
    r=client.get("/game",params={"session_id":session_id,"bet":10000,"lines":2},headers=auth_headers)
    assert r.status_code==400
    assert r.json()["detail"]=="Insufficient balance"


def test_valid_game(client,auth_headers,session_id):
    client.post(f"/session/{session_id}/deposit",params={"amount":10000},headers=auth_headers)

    r=client.get("/game",params={"session_id":session_id,"bet":500,"lines":1},headers=auth_headers)
    data=r.json()

    assert r.status_code==200
    assert "slots" in data
    assert "winnings" in data
    assert "balance" in data
    assert data["bet"]==500
    assert data["lines"]==1


def test_deposit(client,auth_headers,session_id):
    r=client.post(f"/session/{session_id}/deposit",params={"amount":5000},headers=auth_headers)
    data=r.json()

    assert r.status_code==200
    assert data["session_id"]==session_id
    assert data["deposit"]==5000
    assert data["balance"]==5000


def test_invalid_deposit(client,auth_headers,session_id):
    r=client.post(f"/session/{session_id}/deposit",params={"amount":100},headers=auth_headers)
    assert r.status_code==400
    assert r.json()["detail"]=="minimum deposit amount - 500"


def test_invalid_deposit_session(client,auth_headers):
    r=client.post("/session/999999/deposit",params={"amount":5000},headers=auth_headers)
    assert r.status_code==404
    assert r.json()["detail"]=="Invalid session"


def test_unique_sessions(client,auth_headers):
    s1=client.post("/session",headers=auth_headers).json()["session_id"]
    s2=client.post("/session",headers=auth_headers).json()["session_id"]
    assert s1!=s2


def test_game_requires_login(client,session_id):
    r=client.get("/game",params={"session_id":session_id,"bet":500,"lines":1})
    assert r.status_code==401


def test_cannot_use_another_users_session(client,session_id):
    client.post("/register",json={"username":"player2","password":"pw12345"})
    r=client.post("/login",data={"username":"player2","password":"pw12345"})
    other={"Authorization":f"Bearer {r.json()['access_token']}"}

    r=client.get("/game",params={"session_id":session_id,"bet":500,"lines":1},headers=other)
    assert r.status_code==404
    assert r.json()["detail"]=="Invalid session"