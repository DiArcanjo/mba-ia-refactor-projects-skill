import logging

from config.settings import DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, STATUS_DONE, TASK_STATUSES
from controllers import validators
from controllers.transaction import transaction
from database.connection import db, utcnow
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)

CREATE_DATE_ERROR = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_ERROR = 'Formato de data inválido'


def _find_task(task_id):
    task = Task.find(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_user_exists(user_id):
    if not User.find(user_id):
        raise NotFoundError('Usuário não encontrado')


def _ensure_category_exists(category_id):
    if not Category.find(category_id):
        raise NotFoundError('Categoria não encontrada')


def list_tasks():
    return Task.list_with_relations()


def get_task(task_id):
    return _find_task(task_id)


def create_task(data):
    if not data:
        raise ValidationError('Dados inválidos')

    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')

    fields = {
        'title': validators.validate_title(title),
        'description': data.get('description', ''),
        'status': validators.validate_status(data.get('status', DEFAULT_TASK_STATUS)),
        'priority': validators.validate_priority(data.get('priority', DEFAULT_PRIORITY)),
    }

    user_id = data.get('user_id')
    if user_id:
        _ensure_user_exists(user_id)
    category_id = data.get('category_id')
    if category_id:
        _ensure_category_exists(category_id)
    fields['user_id'] = user_id
    fields['category_id'] = category_id

    if data.get('due_date'):
        fields['due_date'] = validators.parse_due_date(data['due_date'], CREATE_DATE_ERROR)
    if data.get('tags'):
        fields['tags'] = validators.normalize_tags(data['tags'])

    task = Task(**fields)
    with transaction('Erro ao criar task'):
        db.session.add(task)
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task


def update_task(task_id, data):
    task = _find_task(task_id)
    if not data:
        raise ValidationError('Dados inválidos')

    changes = {}
    if 'title' in data:
        changes['title'] = validators.validate_title(data['title'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'status' in data:
        changes['status'] = validators.validate_status(data['status'])
    if 'priority' in data:
        changes['priority'] = validators.validate_priority(data['priority'])
    if 'user_id' in data:
        if data['user_id']:
            _ensure_user_exists(data['user_id'])
        changes['user_id'] = data['user_id']
    if 'category_id' in data:
        if data['category_id']:
            _ensure_category_exists(data['category_id'])
        changes['category_id'] = data['category_id']
    if 'due_date' in data:
        due_date = data['due_date']
        changes['due_date'] = (
            validators.parse_due_date(due_date, UPDATE_DATE_ERROR) if due_date else None
        )
    if 'tags' in data:
        changes['tags'] = validators.normalize_tags(data['tags'])

    with transaction('Erro ao atualizar'):
        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = utcnow()
    logger.info('Task atualizada: %s', task.id)
    return task


def delete_task(task_id):
    task = _find_task(task_id)
    with transaction('Erro ao deletar'):
        db.session.delete(task)
    logger.info('Task deletada: %s', task_id)


def search_tasks(text, status, priority, user_id):
    return Task.search(
        text=text,
        status=status,
        priority=validators.parse_priority_filter(priority) if priority else None,
        user_id=validators.parse_user_id_filter(user_id) if user_id else None,
    )


def task_stats():
    status_counts = Task.count_by_status()
    total = sum(status_counts.values())
    done = status_counts.get(STATUS_DONE, 0)
    return {
        'total': total,
        **{status: status_counts.get(status, 0) for status in TASK_STATUSES},
        'overdue': len(Task.find_overdue()),
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
