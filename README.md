https://gist.github.com/joefutrelle/20bc25f566b39ce10db46322a9483a48

# Run client

```shell
$ docker-compose up -d
$ python client.py
```

# Explanation

### Blocking endpoint:
 - Payloads are returned to the client when the task completes
 - Endpoint blocks upon request, tasks are executed synchronously

### Non-blocking endpoint:
 - Task immediately returns a 'status: processing' message and the token
 - Subsequent interrogations of the task reveal the status
 - When the task is completed, the interrogation returns the completed status along with the payload  
