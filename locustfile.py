import random
import time
import uuid

from locust import HttpUser, between, task


def _request_id() -> str:
    return str(uuid.uuid4())


class AppObservabilityUser(HttpUser):
    wait_time = between(0.1, 0.8)

    def on_start(self) -> None:
        self.user_id = None
        self.short_code = []
        self._create_seed_user()

    def _create_seed_user(self) -> None:
        suffix = uuid.uuid4().hex[:10]
        payload = {
            "username": f"locust_{suffix}",
            "email": f"locust_{suffix}@example.com",
        }

        with self.client.post(
            "/users",
            json=payload,
            headers={"X-Request-ID": _request_id()},
            name="POST /users",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                body = response.json()
                self.user_id = body.get("id")
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"unexpected status while creating seed user: {response.status_code}")

    @task(8)
    def list_users(self) -> None:
        with self.client.get(
            "/users?page=1&per_page=25",
            headers={"X-Request-ID": _request_id()},
            name="GET /users",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"unexpected status: {response.status_code}")
                return

            rid = response.headers.get("X-Request-ID")
            if not rid:
                response.failure("missing X-Request-ID header")

    @task(6)
    def list_urls(self) -> None:
        with self.client.get(
            "/urls",
            headers={"X-Request-ID": _request_id()},
            name="GET /urls",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"unexpected status: {response.status_code}")

    @task(8)
    def create_url(self) -> None:
        if not self.user_id:
            self._create_seed_user()
            if not self.user_id:
                return

        payload = {
            "user_id": self.user_id,
            "original_url": "https://example.com/load-test",
            "title": "locust-url",
        }

        with self.client.post(
            "/urls",
            json=payload,
            headers={"X-Request-ID": _request_id()},
            name="POST /urls",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"unexpected status creating url: {response.status_code}")
                return

            body = response.json()
            self.short_code.append(body.get("short_code"))
            if not self.short_code:
                response.failure("missing short_code in create url response")
                return

    @task(6)
    def redirect_url(self) -> None:
        if not self.short_code or len(self.short_code) == 0:
            return
        
        index = random.randrange(len(self.short_code))
        short_code = self.short_code[index]
        with self.client.get(
            f"/urls/{short_code}/redirect",
            headers={"X-Request-ID": _request_id()},
            allow_redirects=False,
            name="GET /urls/{short_code}/redirect",
            catch_response=True,
        ) as response:
            if response.status_code not in [302, 301]:
                response.failure(f"unexpected redirect status: {response.status_code}")

    @task(3)
    def create_event(self) -> None:
        if not self.user_id:
            self._create_seed_user()
            if not self.user_id:
                return

        with self.client.get(
            "/urls",
            headers={"X-Request-ID": _request_id()},
            name="GET /urls (for event)",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure("unable to fetch urls for event")
                return

            urls = response.json()
            if not urls:
                response.success()
                return
            url_id = random.choice(urls).get("id")

        payload = {
            "url_id": url_id,
            "user_id": self.user_id,
            "event_type": random.choice(["click", "view", "redirect"]),
            "details": {"source": "locust"},
        }
        with self.client.post(
            "/events",
            json=payload,
            headers={"X-Request-ID": _request_id()},
            name="POST /events",
            catch_response=True,
        ) as response:
            if response.status_code not in (201, 404):
                response.failure(f"unexpected status creating event: {response.status_code}")
