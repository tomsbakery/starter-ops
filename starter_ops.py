from os import environ
from flask import Flask
from flask import request
from requests import get, post, put

GH_ORG_NAME = environ["GH_ORG_NAME"]
GH_USER_NAME = environ["GH_USER_NAME"]
GH_ACCESS_TOKEN = environ["GH_ACCESS_TOKEN"]
PROTECTIONS_PAYLOAD_DICT = {
    "required_status_checks": None,
    "enforce_admins": True,
    "required_pull_request_reviews": {
        # "dismissal_restrictions": {},
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": True,
        "required_approving_review_count": 2,
        # "bypass_pull_request_allowances": []
    },
    "restrictions": None
}
ISSUE_PAYLOAD_DICT = {
    "title": "Repository protections",
    "body": \
    "Heyo @nrgetik, the following protections were just enabled on the default branch of this "
    +"repository:\n\n"
    +"- No merges of PRs will be allowed prior to at least 2 code reviews\n"
    +"  - No teams or users are exempt from this; it's enforced even for admins\n"
    +"- Automatic dismissal of existing reviews following new PR commit(s)\n"
}

def gh_request(method, resource, payload=None, addtl_headers=None):
    """a function tailored, somewhat, to the GitHub REST API"""
    gh_rest_base_url = "https://api.github.com"
    full_url = f"{gh_rest_base_url}{resource}"
    gh_base_headers = {"Accept": "application/vnd.github.v3+json"}
    full_headers = gh_base_headers|addtl_headers if addtl_headers else gh_base_headers
    match method:
        case "GET":
            res = get(full_url, headers=full_headers,
                    auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
        case "POST":
            res = post(full_url, headers=full_headers, data=payload,
                    auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
        case "PUT":
            res = put(full_url, headers=full_headers, data=payload,
                    auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
        case _:
            return False
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

if __name__ == "__main__":
    app.run(use_reloader=True)
