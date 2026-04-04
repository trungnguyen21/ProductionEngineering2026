def test_list_events(client):
    response = client.get('/events')
    assert response.status_code == 200
    assert isinstance(response.json, list)
