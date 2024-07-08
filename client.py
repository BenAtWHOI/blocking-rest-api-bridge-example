import asyncio
import aiohttp
import json
import requests

DOTENV = {
    'BASE_URL': 'http://localhost:8000'
}

def pretty(response):
    return json.dumps(response.json(), indent=2)

async def fetch(session, url, method='GET', json=None, timeout=10):
    try:
        if method == 'GET':
            async with session.get(url, timeout=timeout) as response:
                return await response.json()
        elif method == 'POST':
            async with session.post(url, json=json, timeout=timeout) as response:
                return await response.json()
    except asyncio.TimeoutError:
        print(f"Request to {url} timed out after {timeout} seconds")
        return None
    except aiohttp.ClientError as e:
        print(f"Error making request to {url}: {e}")
        return None

def test_blocking_endpoint():
    print('======================================')
    print('Testing blocking endpoint\n')
    # Make blocking endpoint call
    url = f'{DOTENV["BASE_URL"]}/api/blocking'
    response = requests.post(url, json={'foo': 'bar', 'baz': 44})
    print(pretty(response))
    # 2. Publish another message that completes before the first
    response = requests.post(url, json={'foo': 'bar', 'baz': 12345})
    print(pretty(response))
    # 3. Observe output - payload of the first endpoint call was returned, but not the second

async def test_non_blocking_endpoint():
    print('======================================')
    print('Testing non-blocking endpoint\n')
    # Make non-blocking endpoint call
    url = f'{DOTENV["BASE_URL"]}/api/non_blocking'
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, url, method='POST', json={'foo': 'bar', 'baz': 999})
        print('Initial response:', json.dumps(response, indent=2))

        token = response['token']

        # Poll for status every second
        while True:
            status_url = f'{DOTENV["BASE_URL"]}/api/status/{token}'
            status = await fetch(session, status_url)
            print('Status: ', json.dumps(status, indent=2))
            if status['status'] == 'completed':
                break
            await asyncio.sleep(1)  
        print(f'Final result: {json.dumps(status, indent=2)}\n')

def main():
    # Run synchronous part
    test_blocking_endpoint()

    # Run asynchronous part
    asyncio.run(test_non_blocking_endpoint())

    print('======================================')
    print('All tests passed.')
    print('======================================')

if __name__ == '__main__':
    main()