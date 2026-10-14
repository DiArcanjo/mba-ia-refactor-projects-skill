import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400

    def __init__(self, mensagem, incluir_sucesso=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.incluir_sucesso = incluir_sucesso


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class NotFoundError(AppError):
    status_code = 404


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def tratar_erro_dominio(erro):
        corpo = {"erro": erro.mensagem}
        if erro.incluir_sucesso:
            corpo["sucesso"] = False
        return jsonify(corpo), erro.status_code

    @app.errorhandler(HTTPException)
    def tratar_erro_http(erro):
        return erro

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(erro):
        logger.exception("Erro inesperado: %s", erro)
        return jsonify({"erro": "Erro interno do servidor"}), 500
