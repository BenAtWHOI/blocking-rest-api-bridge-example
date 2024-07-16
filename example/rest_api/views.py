import aio_pika
import asyncio
import json
import os
import pika
import uuid
from .models import AsyncEventList, RequestPayload, ResponseHolder
from dotenv import load_dotenv
from ninja import NinjaAPI
from starlette.background import BackgroundTasks
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
cached_requests = AsyncEventList()

@api.post("/non_blocking")
async def non_blocking(request, payload: RequestPayload):
    # Create request body
    token = str(uuid.uuid4())
    body = {"token": token, "payload": payload.dict()}
    await cached_requests.set(token, {"status": "processing"})

    # Publish message to AMQP queue
    connection_url = f"amqp://{os.getenv('AMQP_USERNAME')}:{os.getenv('AMQP_PASSWORD')}@{os.getenv('AMQP_HOST')}"
    connection = await aio_pika.connect_robust(connection_url)

    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(os.getenv('AMQP_OUTPUT_CHANNEL_ASYNC'))
        await channel.declare_queue(os.getenv('AMQP_INPUT_CHANNEL_ASYNC'))
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(body).encode()),
            routing_key=os.getenv('AMQP_INPUT_CHANNEL_ASYNC')
        )

    # Immediately return a processing status
    return {"token": token, "status": "processing"}

async def watch_task():
    try:
        connection_url = f"amqp://{os.getenv('AMQP_USERNAME')}:{os.getenv('AMQP_PASSWORD')}@{os.getenv('AMQP_HOST')}"
        connection = await aio_pika.connect_robust(connection_url)
        
        async with connection:
            channel = await connection.channel()
            output_queue = await channel.declare_queue(os.getenv('AMQP_OUTPUT_CHANNEL_ASYNC'))

            async def process_response_async(message: aio_pika.IncomingMessage):
                async with message.process():
                    response = json.loads(message.body)
                    token = response['token']
                    cached_request = await cached_requests.get(token)
                    if cached_request:
                        await cached_requests.set(token, {"status": "complete", "payload": response['payload']})

            async with output_queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await process_response_async(message)
    except Exception as e:
        print(f"Error in watch_task: {e}")

@api.get("/status")
async def status(request):
    token = request.GET['token']
    cached_request = await cached_requests.get(token)
    response = {
        'token': token,
        'status': cached_request['status']
    }
    if response['status'] == 'complete':
        response['payload'] = cached_request['payload']
        await cached_requests.remove(token)

    return response