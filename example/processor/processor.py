import asyncio
import aiosqlite
import json
import os
import random
from amqp.rabbit import aio_subscribe
from dotenv import load_dotenv

load_dotenv()

###############################################################################
async def callback(message):
    # Simulate long running task
    await asyncio.sleep(random.uniform(0, 4))

    # Process the data
    message = json.loads(message)
    token = message['token']
    payload = message['payload']
    response = {'message': f"Successfully foo'd the baz ({payload['baz']})"} #Or some other operation on the data

    # Update status and payload in database
    async with aiosqlite.connect('tasks.db') as conn:
        try:
            await conn.execute("REPLACE INTO processes (token, status, payload) VALUES (?, ?, ?)", (token, "complete", json.dumps(response)))
            await conn.commit()
        finally:
            await conn.close()

###############################################################################
async def run_processor():
    # Watch for incoming tasks
    await aio_subscribe(
        callback,
        os.getenv('AMQP_HOST'),
        os.getenv('AMQP_USERNAME'),
        os.getenv('AMQP_PASSWORD'),
        os.getenv('AMQP_EXCHANGE'),
    )

###############################################################################
if __name__ == '__main__':
    asyncio.run(run_processor())