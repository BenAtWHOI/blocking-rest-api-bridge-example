import json
import time
import os
import pika
import random
from dotenv import load_dotenv

load_dotenv()

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
    run_processor()