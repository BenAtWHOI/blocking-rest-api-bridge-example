https://gist.github.com/joefutrelle/20bc25f566b39ce10db46322a9483a48

# Invocation

```python
python client.py
```

### Explanation

Blocking endpoint:
 - payloads are returned to the client when the task completes
 - endpoint is blocking, taks execute synchronously

Non-blocking endpoint:
 - task immediately returns a 'status: processing' message with the token
 - subsequent interrogations of the task reveal the status
 - when the task is completed, the interrogation returns the completed status along with the payload  
