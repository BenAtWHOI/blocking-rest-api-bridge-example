import asyncio
import aiosqlite
import json
import os
import random
from amqp.rabbit import aio_subscribe
from dotenv import load_dotenv
from message_process import process_message #This represents the generic process that the processor performs on the data

load_dotenv()

###############################################################################
async def callback(message):
    # Simulate long running task
    await asyncio.sleep(random.uniform(0, 4))

    # Process the data
    message = json.loads(message)
    token = message['token']
    payload = message['payload']
    processed_payload = process_message(payload)
    response = {
        'token': token,
        'payload': processed_payload
    }

    # Update status and payload in database
    async with aiosqlite.connect('tasks.db') as conn:
        try:
            await conn.execute("REPLACE INTO processes (token, status, payload) VALUES (?, ?, ?)", (token, "complete", json.dumps(response)))
            await conn.commit()
        finally:
            conn.close()

###############################################################################
async def run_processor():
    # Watch for incoming tasks
    await aio_subscribe(
        callback,
        os.getenv('AMQP_HOST'),
        os.getenv('AMQP_USERNAME'),
        os.getenv('AMQP_PASSWORD'),
        os.getenv('AMQP_EXCHANGE'),
        routing_key=os.getenv('AMQP_INPUT_CHANNEL')
    )

###############################################################################
if __name__ == '__main__':
    asyncio.run(run_processor())