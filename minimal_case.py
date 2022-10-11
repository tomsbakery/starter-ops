from json import dumps

def main(**kwargs):
    return dumps(kwargs)
    # return { "statusCode": 200, "body": "Status OK" }
