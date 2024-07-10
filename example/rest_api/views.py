import json
import os
import pika
import uuid
from .models import RequestPayload, ResponseHolder
from ninja import NinjaAPI
from threading import Thread
from dotenv import load_dotenv

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
def non_blocking(request, payload: RequestPayload):
    token = str(uuid.uuid4())
    body = {"token": token, "payload": payload.dict()}
    cached_requests[token] = {"status": "processing"}
    
    # Publish message to AMQP queue
    credentials = pika.PlainCredentials(os.getenv('AMQP_USERNAME'), os.getenv('AMQP_PASSWORD'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('AMQP_HOST'), credentials=credentials))
    channel = connection.channel()
    
    channel.queue_declare(os.getenv('AMQP_INPUT_CHANNEL'))
    channel.basic_publish(exchange='', routing_key=os.getenv('AMQP_INPUT_CHANNEL'), body=json.dumps(body))
    connection.close()

    # Start another thread to monitor task completion
    thread = Thread(target=watch_task, args=(token,))
    thread.start()
    
    return {"token": token, "status": "processing"}

def watch_task(token):
    credentials = pika.PlainCredentials(os.getenv('AMQP_USERNAME'), os.getenv('AMQP_PASSWORD'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('AMQP_HOST'), credentials=credentials))
    channel = connection.channel()

    # Mark the cached request as complete
    def complete_task(ch, method, properties, body):
        response = json.loads(body)
        if response['token'] == token:
            payload = response['payload']
            cached_requests[token] = {"status": "complete", "payload": payload}
            # Stop consuming after watched task has completed
            ch.stop_consuming()

    # Monitor the output channel to update task status when complete
    channel.queue_declare(os.getenv('AMQP_OUTPUT_CHANNEL'))
    channel.basic_consume(queue=os.getenv('AMQP_OUTPUT_CHANNEL'), on_message_callback=complete_task, auto_ack=True)
    channel.start_consuming()

@api.get("/status")
def status(request):
    token = request.GET['token']
    cached_request = cached_requests[token]
    response = {
        'token': token,
        'status': cached_request['status']
    }
    # If task is complete, add payload to the response and unset the cached request
    if response['status'] == 'complete':
        response['payload'] = cached_request['payload']
        del cached_requests[token]

    return response