import requests

GH_REST_URL = "https://api.github.com"
GH_HEADERS = {"Accept": "application/vnd.github.v3+json"}

def debug_call(res):
    """assemble and return reasonable information about a request/response"""
    # TODO: make this truly serializable at some point (req/res headers/body)
    return {
        "statusCode": res.status_code,
        "body": {
            "request": {
                "url": res.request.url,
                "headers": res.request.headers,
                "body": res.request.body

            },
            "response": {
                "statusCode": res.status_code,
                "url": res.url,
                "reason": res.reason,
                "headers": res.headers,
                "body": res.text
            }
        }
    }

def get(resource, auth: tuple):
    full_url = f"{GH_REST_URL}{resource}"
    try:
        res = requests.get(full_url, headers=GH_HEADERS, auth=auth, timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException:
        # TODO: more sophisticated error handling
        print(debug_call(res))
        return False
    return res

def post(resource, payload, auth: tuple):
    full_url = f"{GH_REST_URL}{resource}"
    try:
        res = requests.post(full_url, headers=GH_HEADERS, data=payload, auth=auth, timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException:
        # TODO: more sophisticated error handling
        print(debug_call(res))
        return False
    return res

def put(resource, payload, auth: tuple):
    full_url = f"{GH_REST_URL}{resource}"
    try:
        res = requests.put(full_url, headers=GH_HEADERS, data=payload, auth=auth, timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException:
        # TODO: more sophisticated error handling
        print(debug_call(res))
        return False
    return res
