from peewee import CharField, DateTimeField, BooleanField, ForeignKeyField
from app.database import BaseModel
from app.models.user import User
import datetime

class Url(BaseModel):
    user = ForeignKeyField(User, backref='urls')
    short_code = CharField(unique=True, index=True)
    original_url = CharField()
    title = CharField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        db_table = 'urls'
