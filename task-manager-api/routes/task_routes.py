from flask import Blueprint, jsonify, request

from controllers import task_controller
from routes.serializers import (
    serialize_task,
    serialize_task_listing,
    serialize_task_with_overdue,
)

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def list_tasks():
    tasks = task_controller.list_tasks()
    return jsonify([serialize_task_listing(task) for task in tasks]), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = task_controller.get_task(task_id)
    return jsonify(serialize_task_with_overdue(task)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    task = task_controller.create_task(request.get_json())
    return jsonify(serialize_task(task)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = task_controller.update_task(task_id, request.get_json())
    return jsonify(serialize_task(task)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task_controller.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    tasks = task_controller.search_tasks(
        request.args.get('q', ''),
        request.args.get('status', ''),
        request.args.get('priority', ''),
        request.args.get('user_id', ''),
    )
    return jsonify([serialize_task(task) for task in tasks]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.task_stats()), 200
