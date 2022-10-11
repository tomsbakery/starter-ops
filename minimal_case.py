from json import dumps
from pprint import pprint

def main(*args, **kwargs):
    print(type(*args))
    print(type(**kwargs))
    pprint(args)
    pprint(kwargs)
    # kwargs["positional"] = args
    # return dumps(kwargs)
    # return { "statusCode": 200, "body": "Status OK" }
