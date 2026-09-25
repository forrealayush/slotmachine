import requests

base_url="http://127.0.0.1:8000"

def test_invalid_bet():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.get(f"{base_url}/game",params={
        "session_id":session,
        "bet":100,
        "lines":1
    })

    assert response.json()["error"]=="Bet must be between 500 and 10000"


def test_invalid_lines():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.get(f"{base_url}/game",params={
        "session_id":session,
        "bet":500,
        "lines":6
    })

    assert response.json()["error"]=="Lines must be between 1 and 5"

def test_invalid_session():
    response=requests.get(f"{base_url}/game",params={
        "session_id":"999999",
        "bet":500,
        "lines":1
    })

    assert response.json()["error"]=="Invalid session"

def test_insufficient_balance():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.get(f"{base_url}/game",params={
        "session_id":session,
        "bet":10000,
        "lines":2
    })

    assert response.json()["error"]=="Insufficient balance"

def test_valid_game():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.get(f"{base_url}/game",params={
        "session_id":session,
        "bet":500,
        "lines":1
    })

    data=response.json()

    assert "slots" in data
    assert "winnings" in data
    assert "balance" in data
    assert data["bet"]==500
    assert data["lines"]==1