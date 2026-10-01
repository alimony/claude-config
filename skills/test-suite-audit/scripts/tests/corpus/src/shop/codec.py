import json


def dumps(order):
    return json.dumps(order, sort_keys=True)


def loads(text):
    return json.loads(text)
