# mongoengine_patch.py
try:
    from flask.json import JSONEncoder
except ImportError:
    from flask.json.provider import DefaultJSONProvider as JSONEncoder

import flask_mongoengine.json

flask_mongoengine.json.JSONEncoder = JSONEncoder
