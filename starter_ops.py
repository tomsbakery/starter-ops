from os import environ
from flask import Flask
import requests

GH_ORG_NAME = environ["GH_ORG_NAME"]
GH_USER_NAME = environ["GH_USER_NAME"]
GH_ACCESS_TOKEN = environ["GH_ACCESS_TOKEN"]

def gh_request(method, resource, payload=None, addtl_headers=None):
    """a function tailored, somewhat, to the GitHub REST API"""
    gh_rest_base_url = "https://api.github.com"
    full_url = f"{gh_rest_base_url}{resource}"
    gh_base_headers = {"Accept": "application/vnd.github.v3+json"}
    full_headers = gh_base_headers|addtl_headers if addtl_headers else gh_base_headers
    match method:
        case "GET":
            res = requests.get(full_url, headers=full_headers,
                    auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
        case "POST":
            res = requests.post(full_url, headers=full_headers, data=payload,
                    auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
        case "PUT":
            res = requests.put(full_url, headers=full_headers, data=payload,
                    auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
        case _:
            return False
    return res

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Hello"

@app.route("/test", methods=["GET"])
def test():
    return gh_request("GET", f"/orgs/{GH_ORG_NAME}/repos").json()

if __name__ == "__main__":
    app.run(use_reloader=True)