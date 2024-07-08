import json
import time
import pika
import random

DOTENV = {
    'AMQP_USERNAME': 'guest',
    'AMQP_PASSWORD': 'guest',
    'AMQP_HOST': 'rabbitmq',
    'AMQP_INPUT_CHANNEL': 'api_input',
    'AMQP_OUTPUT_CHANNEL': 'api_output',
}

def process_message(ch, method, properties, body):
    message = json.loads(body)
    token = message['token']
    baz = message['payload'].get('baz')
    message = f"successfully foo'd the baz ({baz})"
    response = {
        'token': token,
        'payload': {
            f'message': message
        }
    }

    ch.basic_publish(exchange='', routing_key=DOTENV['AMQP_OUTPUT_CHANNEL'], body=json.dumps(response))

    # Simulate long running task
    time.sleep(random.randint(2, 5))
    print(f'[!] Task successfully processed.')

def run_processor():
    credentials = pika.PlainCredentials(DOTENV['AMQP_USERNAME'], DOTENV['AMQP_PASSWORD'])
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=DOTENV['AMQP_HOST'], credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue=DOTENV['AMQP_INPUT_CHANNEL'])
    channel.queue_declare(queue=DOTENV['AMQP_OUTPUT_CHANNEL'])
    channel.basic_consume(queue=DOTENV['AMQP_INPUT_CHANNEL'], on_message_callback=process_message, auto_ack=True)
    print('Processor is waiting for messages')
    channel.start_consuming()

if __name__ == '__main__':
    run_processor()