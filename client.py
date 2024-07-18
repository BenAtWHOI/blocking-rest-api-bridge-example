import json
import os
import random
import requests
import time
from dotenv import load_dotenv
from threading import Thread

###############################################################################
load_dotenv()

def pretty(response):
    return json.dumps(response.json(), indent=2)

###############################################################################
def test_endpoint(url, payload):
    start = time.time()
    time.sleep(random.uniform(0, 2))
    print(f'Thread {payload['baz']} started')
    headers = {'Content-Type': 'application/json'}
    res = requests.post(url, json=payload, headers=headers)
    finish = time.time() - start
    print(f'Thread {payload['baz']} complete ({finish:0.2f}s): {pretty(res)}')

###############################################################################
if __name__ == '__main__':
    print('======================================')
    print('Testing Endpoint')
    start = time.time()

    # Test endpoint 10 times with random delays
    threads = []
    url = f'{os.getenv('BASE_API_URL')}/process'
    for i in range(10):
        payload = {'foo': 'bar', 'baz': i}
        thread = Thread(target=test_endpoint, args=(url, payload))
        threads.append(thread)
        thread.start()
    [thread.join() for thread in threads]

    finish = time.time() - start
    print('======================================')
    print(f'Tests completed in {finish:0.2f} second(s).')
    print('======================================')