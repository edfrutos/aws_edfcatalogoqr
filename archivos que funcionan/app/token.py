from itsdangerous import TimedSerializer as Serializer
from flask import current_app
from app.models import User

def verify_reset_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None
    return User.objects(id=user_id).first()
