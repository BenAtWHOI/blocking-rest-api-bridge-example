import json
import os
import sqlite3
import time
import uuid
from .models import RequestPayload
from dotenv import load_dotenv
from ninja import NinjaAPI
from amqp.rabbit import publish

api = NinjaAPI()
load_dotenv()

TIMEOUT = 30
POLL_INTERVAL = 1


###############################################################################
def retrieve_result(conn, token):
    cursor = conn.cursor()
    res = cursor.execute("SELECT token, status, payload FROM processes WHERE token = ?", (token,)).fetchone()
    conn.close()
    payload = json.loads(res[2])['payload']
    result = {
        'token': res[0],
        'status': res[1],
        'payload': payload
    }
    return result

###############################################################################
@api.post("/process")
def process(request, payload: RequestPayload):
    # Task data
    token = str(uuid.uuid4())
    body = json.dumps({"token": token, "payload": payload.dict()})

    # Write task to db
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO processes (token, status, payload) VALUES (?, ?, ?)", (token, "processing", json.dumps(payload.dict())))
    conn.commit()

    # Publish task to queue
    publish(
        body,
        os.getenv('AMQP_HOST'),
        os.getenv('AMQP_USERNAME'),
        os.getenv('AMQP_PASSWORD'),
        os.getenv('AMQP_EXCHANGE'),
        routing_key=os.getenv('AMQP_INPUT_CHANNEL')
    )

    # Poll db for status
    timer = time.time()
    while (time.time() - timer < TIMEOUT):
        status = cursor.execute("SELECT token, status, payload FROM processes WHERE token = ?", (token,)).fetchone()
        if status and status[0] == "complete":
            # Task is complete, retreive the result, close the connection, and return 
            return retrieve_result(cursor, token)
        time.sleep(POLL_INTERVAL)

    # Task has timed out
    conn.close()
    return {"status": "timeout"}