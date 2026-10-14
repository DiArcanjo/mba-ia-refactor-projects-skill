from flask import Blueprint, jsonify, request

from controllers import usuario_controller
from database.connection import get_db

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar(get_db()), "sucesso": True}), 200


@bp.get("/usuarios/<int:usuario_id>")
def buscar_usuario(usuario_id):
    return jsonify({"dados": usuario_controller.buscar(get_db(), usuario_id), "sucesso": True}), 200


@bp.post("/usuarios")
def criar_usuario():
    usuario_id = usuario_controller.criar(get_db(), request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


@bp.post("/login")
def login():
    usuario = usuario_controller.login(get_db(), request.get_json(silent=True))
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
