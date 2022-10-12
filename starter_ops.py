from base64 import b64encode
from json import dumps
from os import environ
from flask import Flask, jsonify, make_response, request
from ghrest import github as gh

GH_ORG_NAME = environ["GH_ORG_NAME"]
GH_USER_NAME = environ["GH_USER_NAME"]
GH_ACCESS_TOKEN = environ["GH_ACCESS_TOKEN"]
GH_AUTH = (GH_USER_NAME, GH_ACCESS_TOKEN)
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
    repos = []
    for repo in gh.get(f"/orgs/{GH_ORG_NAME}/repos", GH_AUTH).json():
        repos.append(repo["full_name"])
    return make_response(jsonify(repos), 200)

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
        res = []

        branches = gh.get(f"/repos/{owner}/{repo}/branches", GH_AUTH).json()
        if len(branches) > 0:
            # if we already have a default/main branch, protect it
            branch = branches[0]["name"]
            res.append(gh.put(f"/repos/{owner}/{repo}/branches/{branch}/protection",
                        dumps(PROTECTIONS_PAYLOAD_DICT), GH_AUTH))
        else:
            # otherwise, commit a README.md to create a default branch, then protect it
            contents = b64encode(f"# {repo}".encode("utf-8")).decode("utf-8").strip("\n")
            commit_dict = {"branch": "main", "message": "Initial commit", "content": contents}
            res.append(gh.put(f"/repos/{owner}/{repo}/contents/README.md", dumps(commit_dict),
                        GH_AUTH))
            res.append(gh.put(f"/repos/{owner}/{repo}/branches/main/protection",
                        dumps(PROTECTIONS_PAYLOAD_DICT), GH_AUTH))
        # log an issue to the repo describing actions taken
        res.append(gh.post(f"/repos/{owner}/{repo}/issues", dumps(ISSUE_PAYLOAD_DICT), GH_AUTH))

    if False in res:
        return make_response(jsonify({"code": "failure", "status": 500}), 500)
    return make_response(jsonify({"code": "success", "status": 201}), 201)

if __name__ == "__main__":
    app.run(use_reloader=True)
