import aio_pika
import asyncio
import json
import time
import os
import pika
import random
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

###############################################################################
async def run_processor_async():
    connection_url = f"amqp://{os.getenv('AMQP_USERNAME')}:{os.getenv('AMQP_PASSWORD')}@{os.getenv('AMQP_HOST')}"
    connection = await aio_pika.connect_robust(connection_url)

    async with connection:
        channel = await connection.channel()

        # Process message and send to output channel
        async def process_message_async(message: aio_pika.IncomingMessage):
            async with message.process():
                body = message.body.decode()
                data = json.loads(body)
                token = data['token']
                baz = data['payload']['baz']
                message = f"successfully foo'd the baz ({baz})"  # or some other process with the data
                response = {
                    'token': token,
                    'payload': {
                        'message': message
                    }
                }

                # Simulate long running task
                await asyncio.sleep(random.randint(2, 5))

                # Publish the response
                await channel.default_exchange.publish(
                    aio_pika.Message(body=json.dumps(response).encode()),
                    routing_key=os.getenv('AMQP_OUTPUT_CHANNEL_ASYNC')
                )

        # Wait for incoming messages and output response
        input_queue = await channel.declare_queue(os.getenv('AMQP_INPUT_CHANNEL_ASYNC'))
        await channel.declare_queue(os.getenv('AMQP_OUTPUT_CHANNEL_ASYNC'))
        await input_queue.consume(process_message_async)
        await asyncio.Future() 

###############################################################################
def process_message(ch, method, properties, body):
    message = json.loads(body)
    token = message['token']
    baz = message['payload']['baz']
    message = f"successfully foo'd the baz ({baz})" # or some other process with the data
    response = {
        'token': token,
        'payload': {
            f'message': message
        }
    }

    # Simulate long running task
    time.sleep(random.randint(2, 5))
    ch.basic_publish(exchange='', routing_key=os.getenv('AMQP_OUTPUT_CHANNEL'), body=json.dumps(response))

###############################################################################
def run_processor():
    credentials = pika.PlainCredentials(os.getenv('AMQP_USERNAME'), os.getenv('AMQP_PASSWORD'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('AMQP_HOST'), credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue=os.getenv('AMQP_INPUT_CHANNEL'))
    channel.queue_declare(queue=os.getenv('AMQP_OUTPUT_CHANNEL'))
    channel.basic_consume(queue=os.getenv('AMQP_INPUT_CHANNEL'), on_message_callback=process_message, auto_ack=True)
    channel.start_consuming()

###############################################################################
if __name__ == '__main__':
    asyncio.run(run_processor_async())
    # run_processor()