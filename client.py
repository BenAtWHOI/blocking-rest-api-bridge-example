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
def main():
    start = time.time()

    # Test endpoint
    url = f'{os.getenv('BASE_API_URL')}/process'
    payload = {'foo': 'bar', 'baz': 42}
    headers = {'Content-Type': 'application/json'}
    res = requests.post(url, json=payload, headers=headers)
    print(pretty(res))

    finish = time.time() - start
    print('======================================')
    print(f'Tests completed in {finish:0.2f} second(s).')
    print('======================================')

if __name__ == '__main__':
    main()