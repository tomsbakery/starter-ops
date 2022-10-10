# -*- coding: utf-8 -*-

"""
repo creation event triggers this lambda function
sleep for a spell
check for the existence of a default branch in the newly created repo
    if it has one:
        an initial commit was made along with the creation of the repository, protect that branch
    if it doesn't:
        create a README.md in the repo, protect resulting branch
post an issue to the repo stating what just happened
"""

from base64 import b64decode
from base64 import b64encode
from json import dumps
from json import loads
from os import environ
from urllib.parse import unquote
import requests

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
    +"- Dismissal of existing reviews following a new commit\n"
}

def gh_request(action, resource, payload=None, addtl_headers=None):
    """a request function tailored somewhat for GH REST API"""
    gh_rest_base_url = "https://api.github.com"
    full_url = f"{gh_rest_base_url}{resource}"
    gh_base_headers = {"Accept": "application/vnd.github.v3+json"}
    full_headers = gh_base_headers|addtl_headers if addtl_headers else gh_base_headers
    # starting in python 3.10 there's a match/case pattern, but this is probably 3.9
    if action == "GET":
        res = requests.get(full_url, headers=full_headers,
                            auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
    elif action == "POST":
        res = requests.post(full_url, headers=full_headers, data=payload,
                            auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
    elif action == "PUT":
        res = requests.put(full_url, headers=full_headers, data=payload,
                            auth=(GH_USER_NAME, GH_ACCESS_TOKEN))
    else:
        return False
    return res

def request_debug(res):
    """assemble and return reasonable information about a request/response"""
    return {
        "statusCode": res.status_code,
        "body": {
            "request": {
                "url": res.request.url,
                # i would like for this to be sophiscated enough to produce a readable
                # debug payload, but alas the approach has issues of its own
                # "headers": dict(res.request.headers),
                # "body": loads(res.request.body.replace("\\", ""))
                "headers": str(res.request.headers),
                "body": str(res.request.body)

            },
            "response": {
                "statusCode": res.status_code,
                "url": res.url,
                "reason": res.reason,
                # "headers": dict(res.headers),
                # "body": loads(res.text.replace("\\", ""))
                "headers": str(res.headers),
                "body": str(res.text)
            }
        }
    }

def lambda_handler(event, context):
    """handles incoming events from github webhooks"""
    try:
        # actual_event = event # for testing in lambda with bare event payloads
        actual_event = loads(unquote(b64decode(event["body"]))[8:])
    except KeyError:
        return { "statusCode": 400, "body": "Malformed/invalid request" }
    except TypeError:
        return { "statusCode": 400, "body": "Empty request" }

    # GH will push to us on a few repo events, but let's only do stuff when a repo is created
    if actual_event["action"] == "created":
        owner = actual_event["repository"]["owner"]["login"]
        repo = actual_event["repository"]["name"]

        try:
            response = gh_request("GET", f"/repos/{owner}/{repo}/branches")
            response.raise_for_status()
            branches = response.json()
            if len(branches) > 0:
                # if we have a default branch, protect it
                # (maybe it already is protected, but who cares/let's override that)
                branch = branches[0]["name"]
                response = gh_request("PUT", f"/repos/{owner}/{repo}/branches/{branch}/protection",
                            payload=dumps(PROTECTIONS_PAYLOAD_DICT))
                response.raise_for_status()
            else:
                # otherwise, commit a README.md to create a default branch, then protect it
                contents = b64encode(f"# {repo}".encode("utf-8")).decode("utf-8").strip("\n")
                commit_dict = {"branch": "main", "message": "Initial commit", "content": contents}
                response = gh_request("PUT", f"/repos/{owner}/{repo}/contents/README.md",
                            payload=dumps(commit_dict))
                response.raise_for_status()
                response = gh_request("PUT", f"/repos/{owner}/{repo}/branches/main/protection",
                            payload=dumps(PROTECTIONS_PAYLOAD_DICT))
                response.raise_for_status()
            # now let's toss an issue in there to describe what we just did
            response = gh_request("POST", f"/repos/{owner}/{repo}/issues",
                        payload=dumps(ISSUE_PAYLOAD_DICT))
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            return request_debug(response)

    return { "statusCode": 200, "body": "Everything is probably fine" }
