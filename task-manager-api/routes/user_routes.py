from flask import Blueprint, jsonify, request

from controllers import user_controller
from routes.serializers import (
    serialize_task,
    serialize_user,
    serialize_user_task,
    serialize_user_with_task_count,
)

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def list_users():
    rows = user_controller.list_users()
    return jsonify([serialize_user_with_task_count(user, count) for user, count in rows]), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user, tasks = user_controller.get_user(user_id)
    return jsonify({**serialize_user(user), 'tasks': [serialize_task(task) for task in tasks]}), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    user = user_controller.create_user(request.get_json())
    return jsonify(serialize_user(user)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = user_controller.update_user(user_id, request.get_json())
    return jsonify(serialize_user(user)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user_controller.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def list_user_tasks(user_id):
    tasks = user_controller.list_user_tasks(user_id)
    return jsonify([serialize_user_task(task) for task in tasks]), 200


@user_bp.route('/login', methods=['POST'])
def login():
    user, token = user_controller.login(request.get_json())
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': serialize_user(user),
        'token': token,
    }), 200
