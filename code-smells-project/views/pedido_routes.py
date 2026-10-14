from flask import Blueprint, jsonify, request

from controllers import pedido_controller, relatorio_controller
from database.connection import get_db

bp = Blueprint("pedidos", __name__)


@bp.post("/pedidos")
def criar_pedido():
    resultado = pedido_controller.criar(get_db(), request.get_json(silent=True))
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@bp.get("/pedidos")
def listar_todos_pedidos():
    return jsonify({"dados": pedido_controller.listar_todos(get_db()), "sucesso": True}), 200


@bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_controller.listar_por_usuario(get_db(), usuario_id), "sucesso": True}), 200


@bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status_pedido(pedido_id):
    pedido_controller.atualizar_status(get_db(), pedido_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


@bp.get("/relatorios/vendas")
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.relatorio_vendas(get_db()), "sucesso": True}), 200
