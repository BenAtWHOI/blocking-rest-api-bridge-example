import aio_pika
import asyncio
import json
import os
import pika
import uuid
from .models import RequestPayload, ResponseHolder
from dotenv import load_dotenv
from ninja import NinjaAPI
from threading import Thread

###############################################################################
api = NinjaAPI()
load_dotenv()

@api.get("/hello")
def hello(request):
    return {"message": "Hello, world!"}

###############################################################################
@api.post("/blocking")
def blocking(request, payload: RequestPayload):
    credentials = pika.PlainCredentials(os.getenv('AMQP_USERNAME'), os.getenv('AMQP_PASSWORD'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('AMQP_HOST'), credentials=credentials))
    channel = connection.channel()

    # Publish message to AMQP input
    channel.queue_declare(os.getenv('AMQP_INPUT_CHANNEL'))
    token = str(uuid.uuid4())
    body = json.dumps({"token": token, "payload": payload.dict()})
    channel.basic_publish(exchange='', routing_key=os.getenv('AMQP_INPUT_CHANNEL'), body=body)

    # Store response in memory
    response_holder = ResponseHolder()

    def save_response(ch, method, properties, body):
        response = json.loads(body)
        if response.get('token') == token:
            response_holder.response = response
            response_holder.event.set()
            # Stop consuming after correct response
            ch.stop_consuming()

    channel.queue_declare(os.getenv('AMQP_OUTPUT_CHANNEL'))
    channel.basic_consume(queue=os.getenv('AMQP_OUTPUT_CHANNEL'), on_message_callback=save_response, auto_ack=True)
    channel.start_consuming()

    # Wait for response
    if response_holder.event.wait(timeout=15):
        return response_holder.response
    else:
        return {"error": "Response timeout"}
                
###############################################################################
cached_requests = {}

@api.post("/non_blocking")
async def non_blocking(request, payload: RequestPayload):
    token = str(uuid.uuid4())
    body = {"token": token, "payload": payload.dict()}
    cached_requests[token] = {"status": "processing"}

    # Publish message to AMQP queue
    connection_url = f"amqp://{os.getenv('AMQP_USERNAME')}:{os.getenv('AMQP_PASSWORD')}@{os.getenv('AMQP_HOST')}"
    connection = await aio_pika.connect_robust(connection_url)

    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(os.getenv('AMQP_OUTPUT_CHANNEL_ASYNC'))
        await channel.declare_queue(os.getenv('AMQP_INPUT_CHANNEL_ASYNC'))
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(body).encode()),
            routing_key=os.getenv('AMQP_INPUT_CHANNEL_ASYNC'))

    # Start another thread to monitor task completion
    thread = Thread(target=watch_task, args=(token,))
    thread.start()

    return {"token": token, "status": "processing"}

def watch_task(token):
    credentials = pika.PlainCredentials(os.getenv('AMQP_USERNAME'), os.getenv('AMQP_PASSWORD'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('AMQP_HOST'), credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue=os.getenv('AMQP_OUTPUT_CHANNEL_ASYNC'))

    def callback(ch, method, properties, body):
        response = json.loads(body)
        if response['token'] == token:
            cached_requests[token] = {"status": "complete", "payload": response['payload']}
            channel.stop_consuming()

    channel.basic_consume(queue=os.getenv('AMQP_OUTPUT_CHANNEL_ASYNC'), on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

@api.get("/status")
def status(request):
    token = request.GET['token']
    cached_request = cached_requests.get(token, {"status": "not_found"})
    response = {
        'token': token,
        'status': cached_request['status']
    }
    if response['status'] == 'complete':
        response['payload'] = cached_request['payload']
        del cached_requests[token]

    return response