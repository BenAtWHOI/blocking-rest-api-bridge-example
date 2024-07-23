from ninja import Schema
from threading import Event

# Create your models here.

class RequestPayload(Schema):
    foo: str
    baz: int