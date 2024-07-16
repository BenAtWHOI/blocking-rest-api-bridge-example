import json
import time
import os
import random
import sqlite3
from dotenv import load_dotenv
from amqp.rabbit import subscribe

load_dotenv()

###############################################################################
def process_message(message):
    # Simulate long running task
    # time.sleep(random.randint(2, 5))

    # Process message
    message = json.loads(message)
    token = message['token']
    baz = message['payload']['baz']
    message = f"successfully foo'd the baz ({baz})" # or some other process with the data
    response = {
        'token': token,
        'payload': {
            f'message': message
        }
    }

    # Update status and payload in database
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO processes (token, status, payload) VALUES (?, ?, ?)", (token, "complete", json.dumps(response)))
    conn.commit()

###############################################################################
def run_processor():
    # Watch for incoming tasks
    subscribe(
        process_message,
        os.getenv('AMQP_HOST'),
        os.getenv('AMQP_USERNAME'),
        os.getenv('AMQP_PASSWORD'),
        os.getenv('AMQP_EXCHANGE'),
        routing_key=os.getenv('AMQP_INPUT_CHANNEL')
    )

###############################################################################
if __name__ == '__main__':
    run_processor()