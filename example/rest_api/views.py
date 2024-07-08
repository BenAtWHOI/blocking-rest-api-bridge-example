import aio_pika
import asyncio
import json
import pika
import uuid
from ninja import NinjaAPI
from .models import RequestPayload, ResponsePayload, ResponseHolder

###############################################################################
DOTENV = {
    'AMQP_USERNAME': 'guest',
    'AMQP_PASSWORD': 'guest',
    'AMQP_HOST': 'rabbitmq',
    'AMQP_INPUT_CHANNEL': 'api_input',
    'AMQP_OUTPUT_CHANNEL': 'api_output',
}
api = NinjaAPI()

###############################################################################
@api.get("/hello")
def hello(request):
    return {"message": "Hello, world!"}

###############################################################################
@api.post("/blocking")
def blocking(request, payload: RequestPayload):
    credentials = pika.PlainCredentials(DOTENV['AMQP_USERNAME'], DOTENV['AMQP_PASSWORD'])
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=DOTENV['AMQP_HOST'], credentials=credentials))
    channel = connection.channel()

    # Publish message to AMQP input
    channel.queue_declare(DOTENV['AMQP_INPUT_CHANNEL'])
    token = str(uuid.uuid4())
    body = json.dumps({"token": token, "payload": payload.dict()})
    channel.basic_publish(exchange='', routing_key=DOTENV['AMQP_INPUT_CHANNEL'], body=body)

    # Store response in memory
    response_holder = ResponseHolder()

    def callback(ch, method, properties, body):
        response = json.loads(body)
        if response.get('token') == token:
            response_holder.response = response
            response_holder.event.set()
            # Stop consuming after correct response
            ch.stop_consuming()

    channel.queue_declare(DOTENV['AMQP_OUTPUT_CHANNEL'])
    channel.basic_consume(queue=DOTENV['AMQP_OUTPUT_CHANNEL'], on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

    # Wait for response
    if response_holder.event.wait(timeout=15):
        return response_holder.response
    else:
        return {"error": "Response timeout"}
                
###############################################################################
pending_requests = {}
background_task_running = False

@api.post("/non_blocking")
async def non_blocking(request, payload: RequestPayload):
    global background_task_running
    
    # Start background task if not already running
    if not background_task_running:
        background_task_running = True
        asyncio.create_task(listen_for_responses())

    amqp_url = f"amqp://{DOTENV['AMQP_USERNAME']}:{DOTENV['AMQP_PASSWORD']}@{DOTENV['AMQP_HOST']}/"
    connection = await aio_pika.connect_robust(amqp_url)
    channel = await connection.channel()
    await channel.declare_queue(DOTENV['AMQP_INPUT_CHANNEL'])
    token = str(uuid.uuid4())
    pending_requests[token] = {"status": "processing"}
    message = aio_pika.Message(body=json.dumps({"token": token, "payload": payload.dict()}).encode())
    await channel.default_exchange.publish(message, routing_key=DOTENV['AMQP_INPUT_CHANNEL'])
    await connection.close()
    return {"token": token, "status": "processing"}

@api.get("/status/{token}")
def check_status(request, token: str):
    return pending_requests.get(token, {"status": "not found"})

async def listen_for_responses():
    amqp_url = f"amqp://{DOTENV['AMQP_USERNAME']}:{DOTENV['AMQP_PASSWORD']}@{DOTENV['AMQP_HOST']}/"
    while True:
        try:
            connection = await aio_pika.connect_robust(amqp_url)
            channel = await connection.channel()
            queue = await channel.declare_queue(DOTENV['AMQP_OUTPUT_CHANNEL'])

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        response = json.loads(message.body.decode())
                        token = response['token']
                        if token in pending_requests:
                            pending_requests[token] = {"status": "completed", "result": response['payload']}
        except Exception as e:
            print(f"Error in listen_for_responses: {e}")
            await asyncio.sleep(5)
        finally:
            if 'connection' in locals() and not connection.is_closed:
                await connection.close()