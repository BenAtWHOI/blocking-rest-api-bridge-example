from ninja import Schema

# Create your models here.

class RequestPayload(Schema):
    foo: str
    baz: int