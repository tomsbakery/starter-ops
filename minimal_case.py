from json import dumps

def main(*args, **kwargs):
    kwargs["positional"] = args
    return dumps(kwargs)
    # return { "statusCode": 200, "body": "Status OK" }
