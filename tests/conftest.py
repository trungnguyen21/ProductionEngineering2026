import os
import pytest
from app import create_app
from app.database import db
from app.models.user import User
from app.models.url import Url
from app.models.event import Event

# Configure the app explicitly to use testing database so no live data is touched
os.environ["DATABASE_NAME"] = "test_hackathon_db"

@pytest.fixture
def app():
    _app = create_app()
    _app.config.update({
        "TESTING": True,
    })
    
    # Establish isolated environment structure
    db.connect(reuse_if_open=True)
    db.create_tables([User, Url, Event], safe=True)
    
    yield _app
    
    # Wipe isolation table
    db.drop_tables([User, Url, Event], safe=True)
    if not db.is_closed():
        db.close()

@pytest.fixture
def client(app):
    return app.test_client()
