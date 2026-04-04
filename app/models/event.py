from peewee import CharField, DateTimeField, ForeignKeyField
from playhouse.postgres_ext import JSONField
from app.database import BaseModel
from app.models.user import User
from app.models.url import Url
import datetime

class Event(BaseModel):
    url = ForeignKeyField(Url, backref='events')
    user = ForeignKeyField(User, backref='events', null=True)
    event_type = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    details = JSONField(null=True)

    class Meta:
        table_name = 'events'
