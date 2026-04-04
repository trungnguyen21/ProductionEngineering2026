# Database improvements

## 1. Connection pooling
We used `PooledPostgresqlDatabase` for connection pooling, improve the connectivity of the database

## 2. Added timeouts everywhere: reduces hang/ unneccesary waits
- Added timeout for fetching new connection in the pool
- Added timeout for queries

## 3. Retry backoff for transient errors
- Added retry backoff with exponential delay + jitter in `services.py`
- Added retry for services that contact directly with the database