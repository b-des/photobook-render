import threading
from html_to_image import make_previews
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin

app = Flask(__name__, template_folder='./web')
CORS(app)


@app.route("/")
def index():
    return render_template("blank.html")


@app.route("/make-preview")
def previews():
    make_previews(pages=2)
    return "ok"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
