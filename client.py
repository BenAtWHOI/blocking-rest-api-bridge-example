import os
import random
import requests
import time
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

###############################################################################
def test_endpoint(url, payload):
    start = time.time()

    # Delay endpoint for a few seconds for concurrency testing
    time.sleep(random.uniform(0, 6))
    print(f'Thread {payload['baz']} started: {payload}')
    res = requests.post(url, json=payload)

    # Receive token and processed data from the endpoint and record task TTL
    finish = time.time() - start
    print(f'Thread {payload['baz']} complete ({finish:0.2f}s): {res.json()}')

###############################################################################
if __name__ == '__main__':
    print('======================================')
    print('Testing Endpoint')
    start = time.time()

    # Test endpoint multiple times with random delays
    threads = []
    url = f'{os.getenv('BASE_API_URL')}/process'
    for i in range(10):
        payload = {'foo': 'bar', 'baz': i}
        thread = Thread(target=test_endpoint, args=(url, payload))
        threads.append(thread)
        thread.start()

    # Wait for all endpoints to return before finishing
    for thread in threads:
        thread.join()

    finish = time.time() - start
    print('======================================')
    print(f'Tests completed in {finish:0.2f} second(s).')
    print('======================================')