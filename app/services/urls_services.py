import string
import secrets
import datetime

from app.models.url import Url
from app.models.user import User
from app.services.services import retry_db


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


def generate_short_code(length=6):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@retry_db()
def create_url(user_id: int, original_url: str, title: str = None):
    """
    Create a new shortened URL for a given user.
    Raises User.DoesNotExist if user not found.
    """
    Url.create_table(safe=True)

    # Generate unique short code
    while True:
        short_code = generate_short_code()
        if not Url.select().where(Url.short_code == short_code).exists():
            break

    user = User.get(User.id == user_id)

    return Url.create(
        user=user,
        short_code=short_code,
        original_url=original_url,
        title=title,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )


@retry_db()
def list_urls(user_id: int = None):
    """List all URLs, optionally filtered by user_id."""
    Url.create_table(safe=True)
    query = Url.select()
    if user_id is not None:
        query = query.where(Url.user_id == user_id)
    return list(query)


@retry_db()
def get_url_by_id(url_id: int):
    """Get a single URL by ID. Raises Url.DoesNotExist if not found."""
    Url.create_table(safe=True)
    return Url.get(Url.id == url_id)


@retry_db()
def update_url(url_id: int, title: str = None, is_active: bool = None):
    """
    Update an existing URL's fields.
    Raises Url.DoesNotExist if not found.
    """
    Url.create_table(safe=True)
    url = Url.get(Url.id == url_id)

    if title is not None:
        url.title = title
    if is_active is not None:
        url.is_active = is_active

    url.updated_at = datetime.datetime.now()
    url.save()
    return url
