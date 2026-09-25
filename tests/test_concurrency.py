import requests
import concurrent.futures

base_url="http://127.0.0.1:8000"

def test_concurrent_sessions():
    session1=requests.post(f"{base_url}/session").json()["session_id"]
    session2=requests.post(f"{base_url}/session").json()["session_id"]

    requests.post(f"{base_url}/session/{session1}/deposit",params={"amount":10000})
    requests.post(f"{base_url}/session/{session2}/deposit",params={"amount":10000})
    
    def play(session_id):
        response=requests.get(f"{base_url}/game",params={
            "session_id":session_id,
            "bet":500,
            "lines":2
        })
        return response.json()

    session_ids=[session1,session2]*10

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results=list(executor.map(play,session_ids))

    for session_id in [session1,session2]:
        session_results=[
            result for result,used_session in zip(results,session_ids)
            if used_session==session_id and "error" not in result
        ]

        total_bets=sum(r["bet"]*r["lines"] for r in session_results)
        total_winnings=sum(r["winnings"] for r in session_results)
        expected=10000-total_bets+total_winnings

        actual=requests.get(
            f"{base_url}/session/{session_id}"
        ).json()["balance"]

        assert expected==actual