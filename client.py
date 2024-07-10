import json
import os
import requests
import time
from dotenv import load_dotenv

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
        print(f'Polling status: {pretty(response)}')
        status = response.json()['status']

    # Observe output: 
    #  - task immediately returns a 'status: processing' message with the token
    #  - subsequent interrogations of the task reveal the status
    #  - when the task is completed, the interrogation returns the completed status along with the payload  

###############################################################################
def main():
    test_blocking_endpoint()
    test_non_blocking_endpoint()

    print('======================================')
    print('Tests completed.')
    print('======================================')

if __name__ == '__main__':
    main()