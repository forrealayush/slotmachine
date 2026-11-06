from fastapi import FastAPI,HTTPException,Query,Depends,status
from threading import Lock
from game.engine import get_slot_machine_spin,symbol_count,check_winnings,symbol_value
import uuid
from database import SessionLocal
from models import User,GameSession,Bet,Deposit
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime,timedelta,timezone
import csv
from fastapi.responses import FileResponse
import json
from pydantic import BaseModel
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
import os
import jwt
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
import tempfile
from starlette.background import BackgroundTask
app=FastAPI()


session_locks={}
def get_session_lock(session_id:str):
    return session_locks.setdefault(session_id,Lock())
hasher=PasswordHash.recommended()

class RegisterRequest(BaseModel):
    username:str
    password:str

SECRET_KEY=os.environ.get("SLOT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SLOT_SECRET_KEY environment variable is not set")

ALGORITHM="HS256"
ACCESS_TOKEN_MINUTES=30

def create_access_token(username:str):
    expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_MINUTES)
    payload={"sub":username,"exp":expire}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    credentials_error=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate":"Bearer"}
    )

    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_error

    username=payload.get("sub")
    user=db.query(User).filter(User.username==username).first()

    if not user:
        raise credentials_error

    return user     

def require_admin(current_user:User=Depends(get_current_user)):
    if current_user.role!="admin":
        raise HTTPException(status_code=403,detail="Admin access required")
    return current_user   


@app.get("/")
def home():
    return {"message":"slot machine is running"}


@app.post("/register")
def register(data:RegisterRequest,db:Session=Depends(get_db)):
    user=User(
        username=data.username,
        password_hash=hasher.hash(data.password),
        role="player"
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409,detail="Username already taken")
    db.refresh(user)

    return {
        "id":user.id,
        "username":user.username,
        "role":user.role
    }

@app.post("/login")
def login(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    user=db.query(User).filter(User.username==form.username).first()

    if not user or not hasher.verify(form.password,user.password_hash):
        raise HTTPException(status_code=401,detail="invalid username or password")

    token=create_access_token(user.username)

    return {"access_token":token,"token_type":"bearer"}

@app.post("/session")
def create_session(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    session_id=str(uuid.uuid4())

    game_session=GameSession(
        id=session_id,
        user_id=user.id
    )

    db.add(game_session)
    db.commit()


    return {
        "session_id":session_id,
        "username":user.username,
        "balance":user.balance
    }


@app.post("/session/{session_id}/deposit")
def deposit(
    session_id:str,
    amount:int=Query(description="Deposit amount (minimum 500)"),
    current_user:User=Depends(get_current_user),
    db:Session=Depends(get_db)
):
    

    if amount<500:
        raise HTTPException(status_code=400,detail="minimum deposit amount - 500")

    game_session=db.query(GameSession).filter(GameSession.id==session_id).first()

    if not game_session:
        raise HTTPException(status_code=404,detail="Invalid session")
    if game_session.user_id!=current_user.id:
        raise HTTPException(status_code=404,detail="Invalid session")

    user=db.query(User).filter(User.id==game_session.user_id).first()

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    with get_session_lock(session_id):
        db.refresh(user)
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


@app.post("/game")
def game(
    session_id:str,
    bet:int=Query(description="Bet per line (500–10,000)"),
    lines:int=Query(description="Number of paylines (1–5)"),
    current_user:User=Depends(get_current_user),
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


    game_session=db.query(GameSession).filter(GameSession.id==session_id).first()

    if not game_session:
        raise HTTPException(status_code=404,detail="Invalid session")
    if game_session.user_id!=current_user.id:
        raise HTTPException(status_code=404,detail="Invalid session")

    total_bet=bet*lines

    slots=get_slot_machine_spin(3,3,symbol_count)
    winnings,wins=check_winnings(slots,lines,bet,symbol_value)
    net=winnings-total_bet

    with get_session_lock(session_id):
        user=db.query(User).filter(User.id==game_session.user_id).first()
        db.refresh(user)

        balance=user.balance

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
def player_history(username:str,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    user=db.query(User).filter(User.username==username).first()

    if current_user.username!=username and current_user.role!="admin":
        raise HTTPException(status_code=403,detail="Not allowed to view this player")

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
def deposit_history(username:str,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    user=db.query(User).filter(User.username==username).first()

    if current_user.username!=username and current_user.role!="admin":
        raise HTTPException(status_code=403,detail="Not allowed to view this player")

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

@app.get("/admin/stats",dependencies=[Depends(require_admin)])
def admin_stats(days:int=Query(7,ge=1),db:Session=Depends(get_db)):
    total_players=db.query(User).count()
    total_bets=db.query(Bet).all()
    total_spins=len(total_bets)

    today=func.date(func.current_timestamp())
    start_date=datetime.now(timezone.utc)-timedelta(days=days)
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

@app.get("/admin/players",dependencies=[Depends(require_admin)])
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

@app.get("/admin/players/export",dependencies=[Depends(require_admin)])
def export_players(db:Session=Depends(get_db)):
    users=db.query(User).all()

    tmp=tempfile.NamedTemporaryFile("w",newline="",suffix=".csv",delete=False)
    with tmp as file:
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

        return FileResponse(
        tmp.name,
        filename="players.csv",
        background=BackgroundTask(os.remove,tmp.name)
    )

@app.get("/admin/players/export/json",dependencies=[Depends(require_admin)])
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

    tmp=tempfile.NamedTemporaryFile("w",suffix=".json",delete=False)
    with tmp as file:
        json.dump({"players":players},file,indent=4)

    return FileResponse(
        tmp.name,
        filename="players.json",
        background=BackgroundTask(os.remove,tmp.name)
    )

@app.get("/me")
def me(current_user:User=Depends(get_current_user)):
    return {"username":current_user.username,"role":current_user.role}