def process_message(payload):
    baz = payload['baz']
    return {'message': f'Generic operation | message processed ({baz})'}