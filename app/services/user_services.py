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

def get_users(page: int, per_page: int):
    if page is None or per_page is None:
        query = User.select()
    else:
        query = User.select().paginate(page, per_page)
    
    return [serialize_user(user) for user in query]