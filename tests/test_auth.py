def test_register_login_and_me(client):
    r=client.post("/register",json={"username":"alice","password":"pw12345"})
    assert r.status_code==200

    r=client.post("/login",data={"username":"alice","password":"pw12345"})
    assert r.status_code==200
    token=r.json()["access_token"]

    r=client.get("/me",headers={"Authorization":f"Bearer {token}"})
    assert r.status_code==200
    assert r.json()["username"]=="alice"