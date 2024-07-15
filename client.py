import aiohttp
import asyncio
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
def test_blocking_endpoint():
    print('======================================')
    print('Testing blocking endpoint\n')

    # Make blocking endpoint call
    url = f'{os.getenv("BASE_URL")}/api/blocking'
    json = {'foo': 'bar', 'baz': 44}
    start = time.perf_counter()
    response = requests.post(url, json=json)
    finish = time.perf_counter() - start
    print(f'Got response ({finish:0.2f}s): {pretty(response)}')

    # Make a second endpoint call
    json = {'foo': 'foobar', 'baz': 12345}
    start = time.perf_counter()
    response = requests.post(url, json=json)
    finish = time.perf_counter() - start
    print(f'Got response ({finish:0.2f}s): {pretty(response)}')

    # Observe output: 
    #  - payloads are returned to the client when the task completes
    #  - endpoint is blocking, taks execute synchronously

###############################################################################
def test_non_blocking_endpoint():
    print('======================================')
    print('Testing non-blocking endpoint\n')
    
    # Make non blocking endpoint call
    start = time.perf_counter()
    url = f'{os.getenv("BASE_URL")}/api/non_blocking'
    data = {'foo': 'foooooo', 'baz': 7777777}
    response = requests.post(url, json=data)
    token = response.json()['token']
    print(f'Initial response: {pretty(response)}')

    # Interrogate status of call until completed
    url = f'{os.getenv("BASE_URL")}/api/status?token={token}'
    response = requests.get(url)
    status = response.json()['status']
    while status != 'complete':
        time.sleep(1)
        response = requests.get(url)
        status = response.json()['status']
        print(f'Polling status: {pretty(response)}')
    

    finish = time.perf_counter() - start
    print(f'\nTask completed in {finish:0.2f} second(s).')

    # Observe output: 
    #  - task immediately returns a 'status: processing' message with the token
    #  - subsequent interrogations of the task reveal the status
    #  - when the task is completed, the interrogation returns the completed status along with the payload  

###############################################################################
async def test_multiple_non_blocking_endpoint():
    print('======================================')
    print('Testing multiple simultaneous non-blocking endpoint calls\n')

    url = f'{os.getenv("BASE_URL")}/api/non_blocking'
    tasks = []
    for i in range(3):
        data = {'foo': 'bar', 'baz': i}
        task = asyncio.create_task(call_random(i, url, data))
        tasks.append(task)

    # Wait for all tasks to complete or timeout
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=30)  # 2-minute overall timeout
    except asyncio.TimeoutError:
        print("Test timed out after 2 minutes")

    print('======================================')

async def call_random(i, url, data):
    # Call the endpoint after a random amount of time and check status
    await asyncio.sleep(random.randint(0, 5))
    start = time.perf_counter()

    # Initial endpoint call
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            response_json = await response.json()
            token = response_json['token']
            print(f'Thread {i} started: {response_json}')

    # Interrogate status of call until completed or timeout
    status_url = f'{os.getenv("BASE_URL")}/api/status?token={token}'
    start_time = time.time()
    timeout = 60  # 60 seconds timeout
    while time.time() - start_time < timeout:
        async with aiohttp.ClientSession() as session:
            async with session.get(status_url) as response:
                response_json = await response.json()
                status = response_json['status']
                if status == 'complete':
                    finish = time.perf_counter() - start
                    print(f'Thread {i} complete ({finish:0.2f}s): {response_json}')
                    return
                elif status == 'error':
                    print(f'Thread {i} failed: {response_json}')
                    return
        await asyncio.sleep(1)

    print(f'Thread {i} timed out after {timeout} seconds')

    

###############################################################################
def main():
    # start = time.perf_counter()

    # test_blocking_endpoint()
    # test_non_blocking_endpoint()
    asyncio.run(test_multiple_non_blocking_endpoint())

    # finish = time.perf_counter() - start

    print('======================================')
    # print(f'Tests completed in {finish:0.2f} second(s).')
    print('======================================')

if __name__ == '__main__':
    main()