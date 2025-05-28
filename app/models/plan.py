from mongoengine import (
    Document,
    StringField,
    DecimalField,
    ListField,
    IntField,
    DateTimeField,
)
from datetime import datetime

class Plan(Document):
    meta = {
        'collection': 'plans',
        'indexes': [
            'name',
        ]
    }
    name = StringField(required=True, unique=True, max_length=100)
    price = DecimalField(required=True, precision=2, min_value=0.0)
    features = ListField(StringField(max_length=255), default=list)
    duration_days = IntField(required=True, min_value=1)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super(Plan, self).save(*args, **kwargs)

    def __repr__(self):
        return f'<Plan id={self.id} name="{self.name}">'