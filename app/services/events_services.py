import datetime
from app.models.event import Event
from app.models.url import Url
from app.models.user import User
from app.services.services import retry_db


def serialize_event(event):
    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
        "details": event.details
    }


@retry_db()
def list_events():
    """List all events."""
    Event.create_table(safe=True)
    return list(Event.select())


@retry_db()
def create_event(url_id: int, event_type: str, user_id: int = None, details: dict = None):
    """
    Create a new event.
    Raises Url.DoesNotExist if url not found.
    Raises User.DoesNotExist if user_id provided but not found.
    """
    Event.create_table(safe=True)

    url = Url.get(Url.id == url_id)

    user = None
    if user_id is not None:
        user = User.get(User.id == user_id)

    return Event.create(
        url=url,
        user=user,
        event_type=event_type,
        timestamp=datetime.datetime.now(),
        details=details,
    )
