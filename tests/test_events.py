def test_list_events(client):
    response = client.get('/events')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_list_events_filters(client):
    res_url = client.post('/urls', json={"url_hash": "testhash", "original_url": "http://test.com"})
    url_id = res_url.json["id"] if res_url.status_code == 201 else 1

    res_user = client.post('/users', json={"username": "eventuser", "email": "eventuser@a.com"})
    user_id = res_user.json["id"] if res_user.status_code == 201 else 1
    
    # Create events
    client.post('/events', json={"url_id": url_id, "user_id": user_id, "event_type": "click"})
    client.post('/events', json={"url_id": url_id, "user_id": user_id, "event_type": "view"})

    # Filter by url_id
    res_url_id = client.get(f'/events?url_id={url_id}')
    assert res_url_id.status_code == 200

    # Filter by event_type
    res_type = client.get('/events?event_type=click')
    assert res_type.status_code == 200
    for e in res_type.json:
        assert e["event_type"] == "click"

    # Filter by both
    res_both = client.get(f'/events?url_id={url_id}&event_type=click')
    assert res_both.status_code == 200
    for e in res_both.json:
        assert e["event_type"] == "click"
        assert e["url_id"] == url_id
