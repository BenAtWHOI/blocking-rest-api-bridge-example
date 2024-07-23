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
async def insert_task(token, status, payload):
    # Initial insert for task with status of processing
    async with aiosqlite.connect('tasks.db') as db:
        await db.execute("INSERT INTO processes (token, status, payload) VALUES (?, ?, ?)", 
                         (token, status, json.dumps(payload)))
        await db.commit()

async def check_task_status(token):
    # Poll database for status
    async with aiosqlite.connect('tasks.db') as db:
        async with db.execute("SELECT status FROM processes WHERE token = ?", (token,)) as cursor:
            res = await cursor.fetchone()
            return res[0] if res else None

async def check_task_result(token):
    # Poll database for the updated message when task is completed
    async with aiosqlite.connect('tasks.db') as db:
        async with db.execute("SELECT payload FROM processes WHERE token = ?", (token,)) as cursor:
            res = await cursor.fetchone()
            return res[0] if res else None

###############################################################################
@api.post("/process")
async def process(request, payload: RequestPayload):
    token = str(uuid.uuid4())
    body = json.dumps({"token": token, "payload": payload.dict()})

    # Insert task in database
    await insert_task(token, "processing", payload.dict())

    # Publish task to queue
    await aio_publish(
        body,
        os.getenv('AMQP_HOST'),
        os.getenv('AMQP_USERNAME'),
        os.getenv('AMQP_PASSWORD'),
        os.getenv('AMQP_EXCHANGE')
    )

    # Poll db for status until complete
    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time < TIMEOUT):
        status = await check_task_status(token)
        if status == "complete":
            res = await check_task_result(token)
            return {
                "token": token,
                "status": status,
                "payload": json.loads(res)["payload"]
            }
        await asyncio.sleep(POLL_INTERVAL)

    # Request has timed out
    return {"status": "timeout"}