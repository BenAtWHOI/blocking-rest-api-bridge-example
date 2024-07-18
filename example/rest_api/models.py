from ninja import Schema
from threading import Event
from asyncio import Lock

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

class AsyncEventList:
    def __init__(self):
        self.events = {}
        self.lock = Lock()

    async def get(self, token):
        async with self.lock:
            return self.events[token]

    async def set(self, token, data):
        async with self.lock:
            self.events[token] = data
    
    async def remove(self, token):
        async with self.lock:
            del self.events[token]