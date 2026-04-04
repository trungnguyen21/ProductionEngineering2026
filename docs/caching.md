# Hierarchy structure of the cache

| Key Pattern | Value Type | Purpose | TTL (Expiry) |
| :--- | :--- | :--- | :--- |
| `redirect:{short_code}` | JSON Object | Maps short codes to original URLs for the `/redirect` endpoint. | 5 minutes |
| `url:{url_id}` | JSON Object | Stores the full metadata for a specific URL (`GET /urls/:id`). | 5 minutes |
| `urls:list:u{user_id}:a{is_active}` | JSON List | Stores the results of filtered URL listings (`GET /urls`). | 1 minute |