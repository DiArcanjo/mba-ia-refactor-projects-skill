from flask import current_app
from itsdangerous import URLSafeTimedSerializer


def generate_token(user_id):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps({'user_id': user_id})
