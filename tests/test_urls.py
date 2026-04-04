def test_create_url(client):
    user_res = client.post('/users', json={"username": "urluser1", "email": "urluser1@a.com"})
    user_id = user_res.json["id"]
    
    response = client.post('/urls', json={"user_id": user_id, "original_url": "http://example.com", "title": "Test URL"})
    assert response.status_code == 201
    assert response.json["original_url"] == "http://example.com"
    assert "short_code" in response.json

def test_list_urls(client):
    user_res = client.post('/users', json={"username": "urluser2", "email": "urluser2@a.com"})
    user_id = user_res.json["id"]
    client.post('/urls', json={"user_id": user_id, "original_url": "http://x.com", "title": "X"})
    
    res = client.get('/urls')
    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert len(res.json) > 0

def test_get_url(client):
    user_res = client.post('/users', json={"username": "urluser3", "email": "urluser3@a.com"})
    user_id = user_res.json["id"]
    url_res = client.post('/urls', json={"user_id": user_id, "original_url": "http://x.com", "title": "X"})
    url_id = url_res.json["id"]
    
    res = client.get(f'/urls/{url_id}')
    assert res.status_code == 200
    assert res.json["original_url"] == "http://x.com"

def test_update_url(client):
    user_res = client.post('/users', json={"username": "urluser4", "email": "urluser4@a.com"})
    user_id = user_res.json["id"]
    url_res = client.post('/urls', json={"user_id": user_id, "original_url": "http://y.com", "title": "Y"})
    url_id = url_res.json["id"]
    
    res = client.put(f'/urls/{url_id}', json={"title": "Updated Y", "is_active": False})
    assert res.status_code == 200
    assert res.json["title"] == "Updated Y"
    assert res.json["is_active"] is False
