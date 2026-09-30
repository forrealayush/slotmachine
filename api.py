from fastapi import FastAPI,HTTPException,Query,Depends
from threading import Lock
from game.engine import get_slot_machine_spin,symbol_count,check_winnings,symbol_value
import uuid
from database import SessionLocal
from models import User,GameSession,Bet,Deposit
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime,timedelta
import csv
from fastapi.responses import FileResponse
import json


app=FastAPI()

sessions={}
session_locks={}


def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message":"slot machine is running"}


@app.post("/register")
def register(username:str,db:Session=Depends(get_db)):
    user=User(
        username=username,
        password_hash="temporary",
        role="player"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id":user.id,
        "username":user.username,
        "role":user.role
    }


@app.post("/session")
def create_session(username:str,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.username==username).first()

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    session_id=str(uuid.uuid4())

    game_session=GameSession(
        id=session_id,
        user_id=user.id
    )

    db.add(game_session)
    db.commit()

    sessions[session_id]={
        "spins":0,
        "total_won":0,
        "total_lost":0,
        "net_profit":0
    }

    session_locks[session_id]=Lock()

    return {
        "session_id":session_id,
        "username":user.username,
        "balance":user.balance
    }


@app.post("/session/{session_id}/deposit")
def deposit(
    session_id:str,
    amount:int=Query(description="Deposit amount (minimum 500)"),
    db:Session=Depends(get_db)
):
    if session_id not in sessions:
        raise HTTPException(status_code=404,detail="Invalid session")

    if amount<500:
        raise HTTPException(status_code=400,detail="minimum deposit amount - 500")

    game_session=db.query(GameSession).filter(GameSession.id==session_id).first()

    if not game_session:
        raise HTTPException(status_code=404,detail="Invalid session")

    user=db.query(User).filter(User.id==game_session.user_id).first()

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    with session_locks[session_id]:
        user.balance+=amount

        db_deposit=Deposit(
            user_id=user.id,
            amount=amount
        )

        db.add(db_deposit)
        db.commit()

        balance=user.balance

    return {
        "session_id":session_id,
        "deposit":amount,
        "balance":balance
    }


@app.get("/game")
def game(
    session_id:str,
    bet:int=Query(description="Bet per line (500–10,000)"),
    lines:int=Query(description="Number of paylines (1–5)"),
    db:Session=Depends(get_db)
):
    """
    Play the slot machine.

    bet: Bet per line, from 500 to 10,000.
    lines: Number of paylines (1–5).
    """
    if bet<500 or bet>10000:
        raise HTTPException(status_code=400,detail="Bet must be between 500 and 10000")

    if lines<1 or lines>5:
        raise HTTPException(status_code=400,detail="Lines must be between 1 and 5")

    if session_id not in sessions:
        raise HTTPException(status_code=404,detail="Invalid session")

    game_session=db.query(GameSession).filter(GameSession.id==session_id).first()

    if not game_session:
        raise HTTPException(status_code=404,detail="Invalid session")

    total_bet=bet*lines

    slots=get_slot_machine_spin(3,3,symbol_count)
    winnings,wins=check_winnings(slots,lines,bet,symbol_value)
    net=winnings-total_bet

    with session_locks[session_id]:
        user=db.query(User).filter(User.id==game_session.user_id).first()

        balance=user.balance

        if total_bet>balance:
            raise HTTPException(status_code=400,detail="Insufficient balance")

        balance-=total_bet
        balance+=winnings
        user.balance=balance

        db_bet=Bet(
            session_id=session_id,
            bet_amount=bet,
            lines=lines,
            winnings=winnings,
            net_result=net
        )

        db.add(db_bet)
        db.commit()

    return {
        "slots":[" | ".join(slots[c][r] for c in range(3)) for r in range(3)],
        "bet":bet,
        "lines":lines,
        "winnings":winnings,
        "wins":wins,
        "balance":balance
    }


@app.get("/player/{username}/history")
def player_history(username:str,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.username==username).first()

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    history=[]
    total_bets=0
    total_winnings=0
    net_profit=0
    balance=user.balance

    for game_session in user.sessions:
        for bet in game_session.bets:
            total_bets+=bet.bet_amount*bet.lines
            total_winnings+=bet.winnings
            net_profit+=bet.net_result

            history.append({
                "bet_id":bet.id,
                "session_id":game_session.id,
                "bet_amount":bet.bet_amount,
                "lines":bet.lines,
                "winnings":bet.winnings,
                "net_result":bet.net_result,
                "created_at":bet.created_at
            })

    return {
        "username":user.username,
        "total_bets":total_bets,
        "total_winnings":total_winnings,
        "net_profit":net_profit,
        "balance":balance,
        "history":history
    }


@app.get("/player/{username}/deposits")
def deposit_history(username:str,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.username==username).first()

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    deposits=[]

    for deposit in user.deposits:
        deposits.append({
            "deposit_id":deposit.id,
            "amount":deposit.amount,
            "created_at":deposit.created_at
        })

    return {
        "username":user.username,
        "deposits":deposits
    }

@app.get("/admin/stats")
def admin_stats(days:int=Query(7,ge=1),db:Session=Depends(get_db)):
    total_players=db.query(User).count()
    total_bets=db.query(Bet).all()
    total_spins=len(total_bets)

    today=func.date(func.current_timestamp())
    start_date=datetime.utcnow()-timedelta(days=days)
    range_bets=db.query(Bet).filter(Bet.created_at>=start_date).all()
    range_spins=len(range_bets)
    today_bets=db.query(Bet).filter(func.date(Bet.created_at)==today).all()

    range_bets_amount=0
    range_winnings=0

    for bet in range_bets:
      range_bets_amount+=bet.bet_amount*bet.lines
      range_winnings+=bet.winnings

    range_casino_net=range_bets_amount-range_winnings
    players_range=db.query(GameSession.user_id).join(Bet).filter(Bet.created_at>=start_date).distinct().count()

    players_today=db.query(GameSession.user_id).join(Bet).filter(func.date(Bet.created_at)==today).distinct().count()
    spins_today=len(today_bets)

    bets_today=0
    winnings_today=0

    for bet in today_bets:
        bets_today+=bet.bet_amount*bet.lines
        winnings_today+=bet.winnings

    casino_net_today=bets_today-winnings_today

    total_bet_amount=0
    total_winnings=0

    for bet in total_bets:
        total_bet_amount+=bet.bet_amount*bet.lines
        total_winnings+=bet.winnings

    casino_net=total_bet_amount-total_winnings

    return {
        "all_time": {
            "total_players":total_players,
            "total_spins":total_spins,
            "total_bets":total_bet_amount,
            "total_winnings":total_winnings,
            "casino_net":casino_net
        },
        "today": {
            "players":players_today,
            "spins":spins_today,
            "bets":bets_today,
            "winnings":winnings_today,
            "casino_net":casino_net_today
        },
      "date_range": {
            "days":days,
            "players":players_range,
            "spins":range_spins,
            "bets":range_bets_amount,
            "winnings":range_winnings,
            "casino_net":range_casino_net
        }
    }

@app.get("/admin/players")
def admin_players(db:Session=Depends(get_db)):
    users=db.query(User).all()

    players=[]

    for user in users:
        bets=[]

        for game_session in user.sessions:
            for bet in game_session.bets:
                bets.append(bet)

        total_bets=0
        total_winnings=0

        for bet in bets:
            total_bets+=bet.bet_amount*bet.lines
            total_winnings+=bet.winnings

        net_result=total_winnings-total_bets
        total_spins=len(bets)

        players.append({
            "username":user.username,
            "spins":total_spins,
            "total_bets":total_bets,
            "total_winnings":total_winnings,
            "net_result":net_result
        })

    return {
        "players":players
    }

@app.get("/admin/players/export")
def export_players(db:Session=Depends(get_db)):
    users=db.query(User).all()

    with open("players.csv","w",newline="") as file:
        writer=csv.writer(file)
        writer.writerow(["username","spins","total_bets","total_winnings","net_result"])

        for user in users:
            bets=[]

            for game_session in user.sessions:
                for bet in game_session.bets:
                    bets.append(bet)

            total_bets=0
            total_winnings=0

            for bet in bets:
                total_bets+=bet.bet_amount*bet.lines
                total_winnings+=bet.winnings

            net_result=total_winnings-total_bets

            writer.writerow([
                user.username,
                len(bets),
                total_bets,
                total_winnings,
                net_result
            ])

    return FileResponse("players.csv",filename="players.csv")

@app.get("/admin/players/export/json")
def export_players_json(db:Session=Depends(get_db)):
    users=db.query(User).all()

    players=[]

    for user in users:
        bets=[]

        for game_session in user.sessions:
            for bet in game_session.bets:
                bets.append(bet)

        total_bets=0
        total_winnings=0

        for bet in bets:
            total_bets+=bet.bet_amount*bet.lines
            total_winnings+=bet.winnings

        players.append({
            "username":user.username,
            "spins":len(bets),
            "total_bets":total_bets,
            "total_winnings":total_winnings,
            "net_result":total_winnings-total_bets
        })

    with open("players.json","w") as file:
        json.dump({"players":players},file,indent=4)

    return FileResponse("players.json",filename="players.json")