from fastapi import FastAPI,HTTPException,Query 
from threading import Lock
from game.engine import get_slot_machine_spin,symbol_count,check_winnings,symbol_value
import uuid

app=FastAPI()
sessions={}
session_locks={}

@app.get("/")
def home():
    return {"message":"slot machine is running"}

@app.get("/game")
def game(
    session_id:str,
    bet:int=Query(description="Bet per line (500–10,000)"),
    lines:int=Query(description="Number of paylines (1–5)")
):
     """
    Play the slot machine.

    bet: Bet per line, from 500 to 10,000.
    lines: Number of paylines, from 1 to 5.
    """
     if bet<500 or bet>10000:
      raise HTTPException(status_code=400,detail="Bet must be between 500 and 10000")
    
     if lines<1 or lines>5:
      raise HTTPException(status_code=400,detail="Lines must be between 1 and 5")
     if session_id not in sessions:
      raise HTTPException(status_code=404,detail="Invalid session")

     total_bet=bet*lines

     slots=get_slot_machine_spin(3,3,symbol_count)
     winnings,wins=check_winnings(slots,lines,bet,symbol_value)

     with session_locks[session_id]:
         balance=sessions[session_id]["balance"]

         if total_bet>balance:
          raise HTTPException(status_code=400,detail="Insufficient balance")

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
    session_id=str(uuid.uuid4())
    sessions[session_id]={"balance":0}
    session_locks[session_id]=Lock()
    return {"session_id":session_id,"balance":0}

@app.get("/session/{session_id}")
def get_session(session_id:str):
    if session_id not in sessions:
        raise HTTPException(status_code=404,detail="Invalid session")

    return {
        "session_id":session_id,
        "balance":sessions[session_id]["balance"]
    }

@app.post("/session/{session_id}/deposit")
def deposit(session_id:str,amount:int=Query(description="Deposit amount (minimum ₹500)")):   
    if session_id not in sessions:
     raise HTTPException(status_code=404,detail="Invalid session")
    
    if amount<=500:
        raise HTTPException(status_code=400,detail="minimum deposit amount - 500")

    with session_locks[session_id]:
        sessions[session_id]["balance"]+=amount
        balance=sessions[session_id]["balance"]

    return {
        "session_id":session_id,
        "deposit":amount,
        "balance":balance
    }