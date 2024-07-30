import os
import random
import requests
import time
from dotenv import load_dotenv
from threading import Thread


load_dotenv()

POLL_INTERVAL = int(os.getenv('POLL_INTERVAL'))


if __name__ == '__main__':
    start = time.time()
    print('======================================')
    print('Testing non blocking endpoint\n')

    # Make non blocking endpoint call
    url = f'{os.getenv("BASE_API_URL")}/process_blocking'
    data = {'foo': 'foooooo', 'baz': 7777777}
    res = requests.post(url, json=data)
    token = res.json()['token']
    print(f'Initial response: {res.json()}')

    # Interrogate status of call until completed
    url = f'{os.getenv("BASE_API_URL")}/status?token={token}'
    res = requests.get(url)
    status = res.json()['status']
    while status != 'complete':
        time.sleep(POLL_INTERVAL)
        res = requests.get(url)
        status = res.json()['status']
        print(f'Polling status: {res.json()}')

    print('======================================')
    print('Testing multiple endpoints async')

    def test_endpoint(url, payload):
        start = time.time()

        # Delay endpoint for a few seconds for concurrency testing
        time.sleep(random.uniform(0, 6))
        print(f'Thread {payload['baz']} started: {payload}')
        res = requests.post(url, json=payload)

        # Receive token and processed data from the endpoint and record task TTL
        finish = time.time() - start
        print(f'Thread {payload['baz']} complete ({finish:0.2f}s): {res.json()}')

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