from app.models.event import Event
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
