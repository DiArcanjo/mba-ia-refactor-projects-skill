from config.settings import DEFAULT_CATEGORY_COLOR
from controllers.transaction import transaction
from database.connection import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category


def _find_category(category_id):
    category = Category.find(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    return Category.list_with_task_count()


def create_category(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')

    category = Category(
        name=name,
        description=data.get('description', ''),
        color=data.get('color', DEFAULT_CATEGORY_COLOR),
    )
    with transaction('Erro ao criar categoria'):
        db.session.add(category)
    return category


def update_category(category_id, data):
    category = _find_category(category_id)
    if not data:
        raise ValidationError('Dados inválidos')

    with transaction('Erro ao atualizar'):
        for field in ('name', 'description', 'color'):
            if field in data:
                setattr(category, field, data[field])
    return category


def delete_category(category_id):
    category = _find_category(category_id)
    with transaction('Erro ao deletar'):
        db.session.delete(category)
