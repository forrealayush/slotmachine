from fastapi import FastAPI
from threading import Lock
from game.engine import get_slot_machine_spin,symbol_count,check_winnings,symbol_value

app=FastAPI()
sessions={}
session_locks={}

@app.get("/")
def home():
    return {"message":"slot machine is running"}

@app.get("/game")
def game(session_id:str,bet:int,lines:int):
    if bet<500 or bet>10000:
        return {"error":"Bet must be between 500 and 10000"}
    if lines<1 or lines>5:
        return {"error":"Lines must be between 1 and 5"}
    if session_id not in sessions:
        return {"error":"Invalid session"}

    total_bet=bet*lines

    slots=get_slot_machine_spin(3,3,symbol_count)
    winnings,wins=check_winnings(slots,lines,bet,symbol_value)

    with session_locks[session_id]:
        balance=sessions[session_id]["balance"]

        if total_bet>balance:
            return {"error":"Insufficient balance"}

        balance-=total_bet
        balance+=winnings
        sessions[session_id]["balance"]=balance

    return {
        "slots":[" | ".join(slots[c][r] for c in range(3)) for r in range(3)],
        "bet":bet,
        "lines":lines,
        "winnings":winnings,
        "wins":wins,
        "balance":balance
    }
@app.post("/session")
def create_session():
    session_id=str(len(sessions)+1)
    sessions[session_id]={"balance":10000}
    session_locks[session_id]=Lock()
    return {"session_id":session_id,"balance":10000}

@app.get("/session/{session_id}")
def get_session(session_id:str):
    if session_id not in sessions:
        return {"error":"Invalid session"}

    return {
        "session_id":session_id,
        "balance":sessions[session_id]["balance"]
    }