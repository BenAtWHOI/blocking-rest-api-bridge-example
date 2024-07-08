from ninja import Schema
from threading import Event

# Create your models here.

class RequestPayload(Schema):
    foo: str
    baz: int

class ResponsePayload(Schema):
    message: str

class ResponseHolder:
    def __init__(self):
        self.response = None
        self.event = Event()