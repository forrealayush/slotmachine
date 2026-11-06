import concurrent.futures


def make_player(client,username):
    client.post("/register",json={"username":username,"password":"pw12345"})
    r=client.post("/login",data={"username":username,"password":"pw12345"})
    headers={"Authorization":f"Bearer {r.json()['access_token']}"}
    session_id=client.post("/session",headers=headers).json()["session_id"]
    client.post(f"/session/{session_id}/deposit",params={"amount":10000},headers=headers)
    return headers,session_id


def test_concurrent_sessions(client):
    players={
        "alice":make_player(client,"alice"),
        "bob":make_player(client,"bob")
    }

    def play(name):
        headers,session_id=players[name]
        r=client.get(
            "/game",
            params={"session_id":session_id,"bet":500,"lines":2},
            headers=headers
        )
        return name,r.status_code,r.json()

    names=["alice","bob"]*10

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results=list(executor.map(play,names))

    for name in players:
        headers,_=players[name]
        ok=[data for n,status,data in results if n==name and status==200]

        assert len(ok)==10

        total_bets=sum(d["bet"]*d["lines"] for d in ok)
        total_winnings=sum(d["winnings"] for d in ok)
        expected=10000-total_bets+total_winnings

        r=client.get(f"/player/{name}/history",headers=headers)
        assert r.json()["balance"]==expected    