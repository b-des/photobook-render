import threading
from pprint import pprint
from html_to_image import make_previews
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin

app = Flask(__name__, template_folder='./web')
CORS(app)


@app.route("/")
def index():
    return render_template("blank.html")


@app.route("/make-preview", methods=['GET'])
@cross_origin()
def previews():
    domain = request.args.get('domain')
    uid = request.args.get('uid')
    pages = request.args.get('pages')
    warning = ''
    size = None
    if request.args.get('width') and request.args.get('width'):
        size = {'width': request.args.get('width'), 'height': request.args.get('height')}
    else:
        warning = 'Not specified width or/and height of book. Default value(1000x500) was used'
    if domain == '':
        return "Did'nt receive required parameter: <i>domain</i>", 400
    if uid == '':
        return "Did'nt receive required parameter: <i>uid</i>", 400
    if pages == '':
        return "Did'nt receive required parameter: <i>pages</i>", 400
    print(domain)
    #pprint(vars(request))
    response = make_previews(pages=int(pages), domain=domain, uid=uid, size=size)
    response.update({'warning': warning})
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
