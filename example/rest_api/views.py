
import asyncio
import aiosqlite
import json
import os
import uuid
from .models import RequestPayload
from amqp.rabbit import aio_publish
from dotenv import load_dotenv
from ninja import NinjaAPI

###############################################################################
api = NinjaAPI()
load_dotenv()

TIMEOUT = int(os.getenv('TIMEOUT'))
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL'))

###############################################################################
async def async_insert_task(token, status, payload):
    async with aiosqlite.connect('tasks.db') as db:
        await db.execute("INSERT INTO processes (token, status, payload) VALUES (?, ?, ?)", 
                         (token, status, json.dumps(payload)))
        await db.commit()

async def async_check_task_status(token):
    async with aiosqlite.connect('tasks.db') as db:
        async with db.execute("SELECT status, payload FROM processes WHERE token = ?", (token,)) as cursor:
            result = await cursor.fetchone()
            return result if result else (None, None)

###############################################################################
@api.post("/process")
async def process(request, payload: RequestPayload):
    token = str(uuid.uuid4())
    body = json.dumps({"token": token, "payload": payload.dict()})

    # Insert task into database
    await async_insert_task(token, "processing", payload.dict())

    # Publish task to queue
    await aio_publish(
        body,
        os.getenv('AMQP_HOST'),
        os.getenv('AMQP_USERNAME'),
        os.getenv('AMQP_PASSWORD'),
        os.getenv('AMQP_EXCHANGE')
    )

    # Poll db for status
    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time < TIMEOUT):
        status, result = await async_check_task_status(token)
        if status == "complete":
            return {
                "token": token,
                "status": status,
                "message": json.loads(result)["payload"]["message"]
            }
        await asyncio.sleep(POLL_INTERVAL)

    # Request has timed out
    return {"status": "timeout"}

