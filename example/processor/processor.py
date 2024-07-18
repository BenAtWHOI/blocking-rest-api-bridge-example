import json
import time
import os
import random
import sqlite3
from amqp.rabbit import subscribe
from dotenv import load_dotenv
from message_process import process_message #Import the process to be done on the data here

load_dotenv()

###############################################################################
def callback(message):
    # Simulate long running task
    time.sleep(random.randint(1, 3))

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
    conn = sqlite3.connect('tasks.db')
    try:
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO processes (token, status, payload) VALUES (?, ?, ?)", (token, "complete", json.dumps(response)))
        conn.commit()
    finally:
        conn.close()

###############################################################################
def run_processor():
    # Watch for incoming tasks
    subscribe(
        callback,
        os.getenv('AMQP_HOST'),
        os.getenv('AMQP_USERNAME'),
        os.getenv('AMQP_PASSWORD'),
        os.getenv('AMQP_EXCHANGE'),
        routing_key=os.getenv('AMQP_INPUT_CHANNEL')
    )

###############################################################################
if __name__ == '__main__':
    run_processor()