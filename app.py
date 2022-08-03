import logging
import os
import threading
from logging.handlers import TimedRotatingFileHandler

import config
from html_to_image import make_previews, render_book, to_bool
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin
from threading import Thread

# set up logger
isExist = os.path.exists(config.LOG_DIR)
if not isExist:
    os.makedirs(config.LOG_DIR)

handler = TimedRotatingFileHandler(config.LOG_FILE,
                                   when="midnight",
                                   backupCount=5)
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s]: {} %(levelname)s %(message)s'.format(os.getpid()),
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[handler, logging.StreamHandler()])

logger = logging.getLogger()
logger.info(f'Starting app in {config.APP_ENV} environment')
logger.info(f"DOMAINS_DICT_FILE: {config.DOMAINS_DICT_FILE}")


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
    is_users_book = to_bool(request.args.get('userPreview'))
    warning = ''
    size = None
    if request.args.get('width') and request.args.get('width'):
        size = {'width': int(request.args.get('width')), 'height': int(request.args.get('height'))}
    else:
        warning = 'Not specified width or/and height of book. Default value(1000x500) was used'
    if domain == '':
        return "Did'nt receive required parameter: <i>domain</i>", 400
    if uid == '':
        return "Did'nt receive required parameter: <i>uid</i>", 400
    if pages == '':
        return "Did'nt receive required parameter: <i>pages</i>", 400

    response = make_previews(pages=int(pages), domain=domain, uid=uid, size=size, is_user_preview=is_users_book)
    response.update({'warning': warning})
    return jsonify(response)


@app.route("/render", methods=['GET'])
@cross_origin()
def render():
    domain = request.args.get('domain')
    uid = request.args.get('uid')
    pages = request.args.get('pages')
    no_border = to_bool(request.args.get('no_border'))
    warning = ''
    size = None
    if request.args.get('width') and request.args.get('width'):
        size = {'width': int(request.args.get('width')), 'height': int(request.args.get('height'))}
    else:
        warning = 'Not specified width or/and height of book. Default value(1000x500) was used'
    if domain == '':
        return "Did'nt receive required parameter: <i>domain</i>", 400
    if uid == '':
        return "Did'nt receive required parameter: <i>uid</i>", 400
    if pages == '':
        return "Did'nt receive required parameter: <i>pages</i>", 400

    if request.args.get('redirectUrl') is not None:
        thread = Thread(target=render_book, kwargs={'pages': int(pages), 'domain': domain, 'uid': uid, 'size': size, 'no_border': no_border})
        thread.start()
        return render_template("result.html", data=[], redirect=request.args.get('redirectUrl'))
    else:
        print("render_book")
        response = render_book(pages=int(pages), domain=domain, uid=uid, size=size, no_border=no_border)
        response.update({'warning': warning})
        return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8070)
