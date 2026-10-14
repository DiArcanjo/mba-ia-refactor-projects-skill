from flask import Blueprint, jsonify, request

from controllers import category_controller
from routes.serializers import serialize_category, serialize_category_with_task_count

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def list_categories():
    rows = category_controller.list_categories()
    return jsonify([serialize_category_with_task_count(cat, count) for cat, count in rows]), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    category = category_controller.create_category(request.get_json())
    return jsonify(serialize_category(category)), 201


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = category_controller.update_category(category_id, request.get_json())
    return jsonify(serialize_category(category)), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category_controller.delete_category(category_id)
    return jsonify({'message': 'Categoria deletada'}), 200
