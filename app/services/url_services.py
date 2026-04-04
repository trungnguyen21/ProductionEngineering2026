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
