import csv
import io
import peewee
from datetime import datetime

from app.models.user import User
from app.database import db
from app.services.services import retry_db


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


@retry_db()
def get_users(page: int, per_page: int):
    if page is None or per_page is None:
        query = User.select()
    else:
        query = User.select().paginate(page, per_page)

    return [serialize_user(user) for user in query]


@retry_db()
def get_user_by_id(user_id: int):
    """Get a single user by ID. Raises User.DoesNotExist if not found."""
    return User.get(User.id == user_id)


@retry_db()
def create_user(username: str, email: str):
    """Create a new user. Raises peewee.IntegrityError on duplicate."""
    return User.create(username=username, email=email, created_at=datetime.now())


@retry_db()
def update_user(user_id: int, username: str = None, email: str = None):
    """
    Update an existing user's fields.
    Raises User.DoesNotExist if user not found.
    Raises peewee.IntegrityError on duplicate username/email.
    """
    user = User.get(User.id == user_id)

    if username is not None:
        user.username = username
    if email is not None:
        user.email = email

    user.save()
    return user


@retry_db()
def delete_user(user_id: int):
    """Delete a user by ID. Raises User.DoesNotExist if not found."""
    user = User.get(User.id == user_id)
    user.delete_instance()
    return user


@retry_db()
def bulk_import_users(file_stream):
    """
    Import users from a CSV file stream.
    Returns the number of imported users.
    """
    stream = io.StringIO(file_stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)

    users_to_insert = []
    for row in csv_input:
        try:
            created_at = datetime.strptime(row['created_at'], "%Y-%m-%d %H:%M:%S")
        except (ValueError, KeyError):
            created_at = datetime.now()

        users_to_insert.append({
            'id': int(row['id']),
            'username': row['username'],
            'email': row['email'],
            'created_at': created_at
        })

    with db.atomic():
        for batch in peewee_chunked(users_to_insert, 100):
            User.insert_many(batch).on_conflict_ignore().execute()

    return len(users_to_insert)
