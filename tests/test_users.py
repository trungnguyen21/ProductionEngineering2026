import io

def test_create_user(client):
    response = client.post('/users', json={"username": "user1", "email": "user1@a.com"})
    assert response.status_code == 201
    assert response.json["username"] == "user1"

def test_create_duplicate_user(client):
    response1 = client.post('/users', json={"username": "duplicate_user", "email": "duplicate@a.com"})
    assert response1.status_code == 201
    user_id = response1.json["id"]

    response2 = client.post('/users', json={"username": "duplicate_user", "email": "duplicate@a.com"})
    assert response2.status_code == 201
    assert response2.json["id"] == user_id
    assert response2.json["username"] == "duplicate_user"

def test_create_user_invalid(client):
    response = client.post('/users', json={"username": 123, "email": "userinvalid@a.com"})
    assert response.status_code == 400
    assert "error" in response.json

def test_list_users(client):
    client.post('/users', json={"username": "user2", "email": "user2@a.com"})
    response = client.get('/users?page=1&per_page=10')
    assert response.status_code == 200
    assert "users" in response.json
    assert len(response.json["users"]) > 0

def test_get_user(client):
    res_create = client.post('/users', json={"username": "user3", "email": "user3@a.com"})
    user_id = res_create.json["id"]
    
    res = client.get(f'/users/{user_id}')
    assert res.status_code == 200
    assert res.json["username"] == "user3"

def test_update_user(client):
    res_create = client.post('/users', json={"username": "user4", "email": "user4@a.com"})
    user_id = res_create.json["id"]
    
    res = client.put(f'/users/{user_id}', json={"username": "user4_updated"})
    assert res.status_code == 200
    assert res.json["username"] == "user4_updated"

def test_upload_users(client):
    csv_data = "id,username,email,created_at\n100,testbulk,testbulk@a.com,2025-01-01 00:00:00"
    data = {"file": (io.BytesIO(csv_data.encode()), "test.csv")}
    response = client.post('/users/bulk', data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    assert response.json["imported"] == 1
