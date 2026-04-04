import os
import io
import pytest

def test_full_user_and_url_lifecycle(client):
    # 1. Create a user
    resp = client.post('/users', json={
        "username": "integration_user",
        "email": "integration@test.com"
    })
    assert resp.status_code == 201
    user_id = resp.json["id"]
    
    # 2. Get the user and verify
    resp = client.get(f'/users/{user_id}')
    assert resp.status_code == 200
    assert resp.json["username"] == "integration_user"
    
    # 3. Create a URL for this user
    resp = client.post('/urls', json={
        "user_id": user_id,
        "original_url": "https://www.google.com",
        "title": "Google"
    })
    assert resp.status_code == 201
    url_id = resp.json["id"]
    short_code = resp.json["short_code"]
    
    # 4. List URLs for this user
    resp = client.get(f'/urls?user_id={user_id}')
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["id"] == url_id
    
    # 5. Update the URL
    resp = client.put(f'/urls/{url_id}', json={
        "title": "Google Search",
        "is_active": False
    })
    assert resp.status_code == 200
    assert resp.json["title"] == "Google Search"
    assert resp.json["is_active"] is False

def test_bulk_user_upload_integration(client):
    # Prepare CSV data
    csv_content = "id,username,email,created_at\n100,user100,user100@test.com,2025-01-01 12:00:00\n101,user101,user101@test.com,2025-01-02 12:00:00"
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'users.csv')
    }
    
    # Upload bulk
    resp = client.post('/users/bulk', data=data, content_type='multipart/form-data')
    assert resp.status_code == 201
    assert resp.json["imported"] == 2
    
    # Verify users exist
    resp = client.get('/users/100')
    assert resp.status_code == 200
    assert resp.json["username"] == "user100"
    
    resp = client.get('/users/101')
    assert resp.status_code == 200
    assert resp.json["username"] == "user101"

def test_create_url_for_non_existent_user(client):
    resp = client.post('/urls', json={
        "user_id": 99999,
        "original_url": "https://error.com",
        "title": "Error"
    })
    assert resp.status_code == 404
    assert "User 99999 not found" in resp.json["error"]

def test_user_pagination_integration(client):
    # Create 5 users
    for i in range(5):
        client.post('/users', json={
            "username": f"page_user_{i}",
            "email": f"page_{i}@test.com"
        })
    
    # Test pagination
    resp = client.get('/users?page=1&per_page=2')
    assert resp.status_code == 200
    assert len(resp.json["users"]) == 2
    
    resp = client.get('/users?page=2&per_page=2')
    assert resp.status_code == 200
    assert len(resp.json["users"]) == 2
