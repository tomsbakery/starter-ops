# from json import dumps
from pprint import pprint

def main(*args):
    print(type(args))
    print(len(args))
    pprint(args)
    # kwargs["positional"] = args
    # return dumps(kwargs)
    # return { "statusCode": 200, "body": "Status OK" }
