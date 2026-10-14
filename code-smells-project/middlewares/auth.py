from functools import wraps

from flask import current_app, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from config.settings import TIPO_USUARIO_ADMIN
from middlewares.error_handler import UnauthorizedError


def _serializador():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def gerar_token(usuario):
    return _serializador().dumps({"usuario_id": usuario["id"], "tipo": usuario["tipo"]})


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        cabecalho = request.headers.get("Authorization", "")
        if not cabecalho.startswith("Bearer "):
            raise UnauthorizedError("Acesso restrito a administradores")
        try:
            payload = _serializador().loads(
                cabecalho[len("Bearer "):], max_age=current_app.config["TOKEN_MAX_AGE"]
            )
        except BadSignature:
            raise UnauthorizedError("Acesso restrito a administradores")
        if payload.get("tipo") != TIPO_USUARIO_ADMIN:
            raise UnauthorizedError("Acesso restrito a administradores")
        return view(*args, **kwargs)
    return wrapper
