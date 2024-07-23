def process_message(payload):
    baz = payload['baz']
    return {'message': f"Successfully foo'd the baz ({baz})"}