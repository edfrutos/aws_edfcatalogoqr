# mongoengine_patch.py
from flask.json import JSONEncoder as BaseJSONEncoder

class CustomJSONEncoder(BaseJSONEncoder):
    pass

import flask_mongoengine.json

flask_mongoengine.json.JSONEncoder = CustomJSONEncoder