from base64 import b64encode
from json import dumps
from os import environ
from flask import Flask, jsonify, make_response, request
import requests

GH_ORG_NAME = environ["GH_ORG_NAME"]
GH_USER_NAME = environ["GH_USER_NAME"]
GH_ACCESS_TOKEN = environ["GH_ACCESS_TOKEN"]
PROTECTIONS_PAYLOAD_DICT = {
    "required_status_checks": None,
    "enforce_admins": True,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": True,
        "required_approving_review_count": 2,
    },
    "restrictions": None
}
ISSUE_PAYLOAD_DICT = {
    "title": "Repository protections",
    "body": \
    "Heyo @nrgetik, the following protections were just enabled on the default branch of this "
    +"repository:\n\n"
    +"- Pull requests will be required before merging\n"
    +"- No merges of pull requests allowed prior to at least 2 code reviews by code owners\n"
    +"- Automatic dismissal of existing reviews following new pull request commit(s)\n"
    +"- No teams or users are exempt; these rules apply even for admins"
}

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

def gh_request(method, resource, payload=None, addtl_headers=None):
    """a function tailored, somewhat, to the GitHub REST API"""
    gh_rest_base_url = "https://api.github.com"
    full_url = f"{gh_rest_base_url}{resource}"
    gh_base_headers = {"Accept": "application/vnd.github.v3+json"}
    full_headers = gh_base_headers|addtl_headers if addtl_headers else gh_base_headers
    try:
        match method:
            case "GET":
                res = requests.get(full_url, headers=full_headers,
                        auth=(GH_USER_NAME, GH_ACCESS_TOKEN), timeout=10)
            case "POST":
                res = requests.post(full_url, headers=full_headers, data=payload,
                        auth=(GH_USER_NAME, GH_ACCESS_TOKEN), timeout=10)
            case "PUT":
                res = requests.put(full_url, headers=full_headers, data=payload,
                        auth=(GH_USER_NAME, GH_ACCESS_TOKEN), timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException:
        print(debug_call(res))
        # do some more sophisticated error handling
    return res

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """returns a simple response to show that the app is up and running"""
    return "Hello"

@app.route("/test", methods=["GET"])
def test():
    """
    returns a JSON payload containing the list of repositories in our
    org to test if the REST API interface to GitHub is generally working
    """
    return gh_request("GET", f"/orgs/{GH_ORG_NAME}/repos").json()

@app.route("/oven", methods=["POST"])
def oven():
    """
    receives incoming webhook payloads from new repository events
    and takes the necessary actions to issue our protections using the
    GitHub REST API
    """
    event_dict = request.json

    # GH will push to us on a few repo events, but we only care when a repo is created
    if event_dict["action"] == "created":
        owner = event_dict["repository"]["owner"]["login"]
        repo = event_dict["repository"]["name"]

        branches = gh_request("GET", f"/repos/{owner}/{repo}/branches").json()
        if len(branches) > 0:
            # if we already have a default/main branch, protect it
            branch = branches[0]["name"]
            gh_request("PUT", f"/repos/{owner}/{repo}/branches/{branch}/protection",
                payload=dumps(PROTECTIONS_PAYLOAD_DICT))
        else:
            # otherwise, commit a README.md to create a default branch, then protect it
            contents = b64encode(f"# {repo}".encode("utf-8")).decode("utf-8").strip("\n")
            commit_dict = {"branch": "main", "message": "Initial commit", "content": contents}
            gh_request("PUT", f"/repos/{owner}/{repo}/contents/README.md",
                payload=dumps(commit_dict))
            gh_request("PUT", f"/repos/{owner}/{repo}/branches/main/protection",
                payload=dumps(PROTECTIONS_PAYLOAD_DICT))
        # log an issue to the repo describing actions taken
        gh_request("POST", f"/repos/{owner}/{repo}/issues", payload=dumps(ISSUE_PAYLOAD_DICT))

    return make_response(jsonify({"code": "success", "status": 201}), 201)

if __name__ == "__main__":
    app.run(use_reloader=True)
