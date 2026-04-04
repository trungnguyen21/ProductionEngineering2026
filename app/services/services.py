from peewee import fn
from playhouse.shortcuts import model_to_dict
from app.models.user import User

def peewee_chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

def serialize_user(user):
    dt_str = user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else str(user.created_at)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": dt_str.replace(" ", "T")
    }

def serialize_event(event):
    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
        "details": event.details
    }

def serialize_url(url):
    return {
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat() if hasattr(url.created_at, 'isoformat') else str(url.created_at),
        "updated_at": url.updated_at.isoformat() if hasattr(url.updated_at, 'isoformat') else str(url.updated_at)
    }



def get_users(page: int, per_page: int):
    if page is None or per_page is None:
        query = User.select()
    else:
        query = User.select().paginate(page, per_page)
    
    return [serialize_user(user) for user in query]