from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello"

@app.route("/test")
def test():
    return "There is an app at this endpoint"

if __name__ == '__main__':
    app.run(use_reloader=True)