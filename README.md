https://gist.github.com/joefutrelle/20bc25f566b39ce10db46322a9483a48

# Run client

```shell
$ docker-compose build && docker-compose up
$ python client.py
```

# Explanation

1. Client calls the endpoint simultaneously in different threads
2. API creates a token and adds the task to the database with a "processing" status
3. API publishes a message with the token and payload to a rabbitmq exchange
4. The processor receves the message published by the API
5. The processor sleeps for a few seconds to simulate a long running task and performs some operation on the payload, and publishes the token, the transformed data, and a "complete" status to the database
6. While the processor is working, the API polls the database for status until it receives "complete", and returns the payload and token to the client
