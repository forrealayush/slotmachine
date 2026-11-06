import os
os.environ["SLOT_SECRET_KEY"]="test-secret-key-for-tests-only-0123456789"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from api import app,get_db,session_locks
from models import Base


@pytest.fixture
def client(tmp_path):
    engine=create_engine(
        f"sqlite:///{tmp_path/'test.db'}",
        connect_args={"check_same_thread":False}
    )
    Base.metadata.create_all(engine)
    TestingSession=sessionmaker(bind=engine)

    def override_get_db():
        db=TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db]=override_get_db
    session_locks.clear()

    yield TestClient(app)

    app.dependency_overrides.clear()
    engine.dispose()

@pytest.fixture
def auth_headers(client):
    client.post("/register",json={"username":"player1","password":"pw12345"})
    r=client.post("/login",data={"username":"player1","password":"pw12345"})
    return {"Authorization":f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def session_id(client,auth_headers):
    r=client.post("/session",headers=auth_headers)
    return r.json()["session_id"]    