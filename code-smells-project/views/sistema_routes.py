from flask import Blueprint, current_app, jsonify

from controllers import sistema_controller
from database.connection import get_db
from middlewares.auth import admin_required

bp = Blueprint("sistema", __name__)


@bp.get("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": current_app.config["APP_VERSION"],
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


@bp.get("/health")
def health_check():
    resultado = sistema_controller.health(
        get_db(), current_app.config["APP_VERSION"], current_app.config["APP_ENV"]
    )
    return jsonify(resultado), 200


@bp.post("/admin/reset-db")
@admin_required
def reset_database():
    sistema_controller.resetar_banco(get_db())
    current_app.logger.warning("Banco de dados resetado")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
