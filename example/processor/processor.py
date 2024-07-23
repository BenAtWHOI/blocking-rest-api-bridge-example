import asyncio
import aiosqlite
import json
import time
import os
import random
import sqlite3
import sys
from amqp.rabbit import aio_subscribe
from dotenv import load_dotenv
from message_process import process_message #Import the process to be done on the data here

load_dotenv()

###############################################################################
async def callback(message):
    # Simulate long running task
    asyncio.sleep(random.randint(2, 5))

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

    # Keep processor running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Processor shutting down...")

###############################################################################
if __name__ == '__main__':
    global p_id 
    p_id = sys.argv[1]
    print(f'Processor {p_id} started')
    asyncio.run(run_processor())