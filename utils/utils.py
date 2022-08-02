from PIL import Image, ImageFilter
from flask import Request

import config


def load_domains_dict():
    import json
    # Opening JSON file
    f = open(config.DOMAINS_DICT_FILE)
    # returns JSON object as
    # a dictionary
    data = json.load(f)
    # Closing file
    f.close()
    return data


def get_image_path_from_request(request: Request, domains: dict):
    host = request.origin.split("//")[1]
    path = domains.get(host)
    if not path:
        raise Exception(f"The domain '{host}' is not recognized in domains dictionary")
    return path, host
