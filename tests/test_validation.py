import requests

base_url="http://127.0.0.1:8000"

def test_invalid_bet():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.get(f"{base_url}/game",params={
        "session_id":session,
        "bet":100,
        "lines":1
    })

    assert response.status_code==400
    assert response.json()["detail"]=="Bet must be between 500 and 10000"


def test_invalid_lines():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.get(f"{base_url}/game",params={
        "session_id":session,
        "bet":500,
        "lines":6
    })

    assert response.status_code==400
    assert response.json()["detail"]=="Lines must be between 1 and 5"


def test_invalid_session():
    response=requests.get(f"{base_url}/game",params={
        "session_id":"999999",
        "bet":500,
        "lines":1
    })

    assert response.status_code==404
    assert response.json()["detail"]=="Invalid session"

def test_insufficient_balance():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.get(f"{base_url}/game",params={
        "session_id":session,
        "bet":10000,
        "lines":2
    })

    assert response.status_code==400
    assert response.json()["detail"]=="Insufficient balance"

def test_valid_game():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    requests.post(
        f"{base_url}/session/{session}/deposit",
        params={"amount":10000}
    )

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

def test_deposit():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.post(
        f"{base_url}/session/{session}/deposit",
        params={"amount":5000}
    )

    data=response.json()

    assert data["session_id"]==session
    assert data["deposit"]==5000
    assert data["balance"]==5000    

def test_invalid_deposit():
    session=requests.post(f"{base_url}/session").json()["session_id"]

    response=requests.post(
        f"{base_url}/session/{session}/deposit",
        params={"amount":0}
    )

    assert response.status_code==400
    assert response.json()["detail"]=="Deposit must be greater than 0"    

def test_invalid_deposit_session():
    response=requests.post(
        f"{base_url}/session/999999/deposit",
        params={"amount":5000}
    )

    assert response.status_code==404
    assert response.json()["detail"]=="Invalid session"    

def test_unique_sessions():
    session1=requests.post(f"{base_url}/session").json()["session_id"]
    session2=requests.post(f"{base_url}/session").json()["session_id"]

    assert session1!=session2    


def test_invalid_session_balance():
    response=requests.get(f"{base_url}/session/999999")

    assert response.status_code==404
    assert response.json()["detail"]=="Invalid session"