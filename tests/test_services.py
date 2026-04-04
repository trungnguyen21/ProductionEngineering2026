import datetime
from app.models.user import User
from app.models.url import Url
from app.models.event import Event
from app.services.user_services import serialize_user
from app.services.url_services import serialize_url
from app.services.event_services import serialize_event

def test_serialize_user(app):
    user = User(id=1, username="test", email="test@test.com", created_at=datetime.datetime(2025, 1, 1))
    data = serialize_user(user)
    assert data["id"] == 1
    assert data["username"] == "test"
    assert data["email"] == "test@test.com"
    assert data["created_at"] == "2025-01-01T00:00:00"

def test_serialize_url(app):
    url = Url(id=1, user_id=2, short_code="abcDEF", original_url="http://a.com", title="A", is_active=True, created_at=datetime.datetime(2025, 1, 1), updated_at=datetime.datetime(2025, 1, 2))
    data = serialize_url(url)
    assert data["id"] == 1
    assert data["user_id"] == 2
    assert data["short_code"] == "abcDEF"
    assert data["title"] == "A"
    assert data["is_active"] is True
    assert data["created_at"] == "2025-01-01T00:00:00"
    assert data["updated_at"] == "2025-01-02T00:00:00"

def test_serialize_event(app):
    event = Event(id=1, url_id=1, user_id=None, event_type="click", timestamp=datetime.datetime(2025, 1, 1), details={"browser": "chrome"})
    data = serialize_event(event)
    assert data["id"] == 1
    assert data["url_id"] == 1
    assert data["user_id"] is None
    assert data["event_type"] == "click"
    assert data["details"]["browser"] == "chrome"
    assert data["timestamp"] == "2025-01-01T00:00:00"
