from flask import Flask, render_template, request, Response, stream_with_context
from flask_cors import CORS

import engine

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods = ["POST"])
def chat():
    message = request.json.get("message")
    context = engine.get_context(message)
    return Response(stream_with_context(engine.answer(message, context)), content_type = "text/plain")

if __name__ == "__main__":
    app.run(debug = True, port = 4000)
